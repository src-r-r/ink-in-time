import typing as T
from flask import Flask, render_template, request, abort, Request
from datetime import datetime, timedelta
from urllib.parse import parse_qs, parse_qsl
from werkzeug.serving import is_running_from_reloader
import time
import os
import atexit
from calendar import month_name as MN
import pytz
import arrow
from multiprocessing import Process
from pathlib import Path
import logging

from .config import config
from .core import COMPILEPID_FILE, MOCK_ICS_DIR
from .checker import check_config
from .db import fetch_more_human_choices
from .calendar import calblock_choices
from .db import compile_choices, get_lastrun_primary
from .email import AppointmentRequest

log = logging.getLogger(__name__)


TPL_BASE = Path("iit")
IDX_TPL = TPL_BASE / "index"
INC_TPL = TPL_BASE / "inc"
INDEX_TEMPLATE = IDX_TPL / "timeblock_selection.html"
CONFIRM_TEMPLATE = IDX_TPL / "confirmation.html"

CHOICE_TPL_DIR = INC_TPL / "choice"
BLOCK_CHOICE_TPL = CHOICE_TPL_DIR / "appointment_type.html"
YEAR_CHOICE_TPL = CHOICE_TPL_DIR / "year.html"
MONTH_CHOICE_TPL = CHOICE_TPL_DIR / "month.html"
DAY_CHOICE_TPL = CHOICE_TPL_DIR / "day.html"


STEPS = [
    "/",
    "/<string:block>/",
    "/<string:block>/<int:year>/",
    "/<string:block>/<int:year>/<int:month>/",
    "/<string:block>/<int:year>/<int:month>/<int:day>/",
]
GET = "GET"
POST = "POST"


def template_exists(tpl: Path):
    return (Path("templates") / tpl).exists()


def template_if_exists(tpl: Path):
    if template_exists(tpl):
        return str(tpl)
    return None


def add_error(context: T.Dict, field: T.AnyStr, code: T.AnyStr):
    errors = context.get("errors", {})
    errors.update(
        {
            field: code,
        }
    )
    context["has_errors"] = True
    context["errors"] = errors
    return context


# callback functions


def run_compile_job(request=None):
    """Compile the calendars & blocks together

    This is supposed to behave like a task qeue, but minimized.

    Args:
        request (flask.Request, optional): Only used to keep flask happy. Defaults to None.
    """
    lastrun = get_lastrun_primary()
    interval = config.db_compilation_interval
    now = arrow.utcnow()
    do_run = False
    if lastrun is None:
        do_run = True
    else:
        log.debug("not compiling -- hasn't been long enough")
        do_run = now - lastrun > interval
    if not do_run:
        return request
    log.info("kicking off compilation job")
    if COMPILEPID_FILE.exists():
        log.warning("%s exists, not running", COMPILEPID_FILE)
        return request
    proc = Process(target=compile_choices)
    # Delay writing to the file for a bit to delay the reloader
    proc.start()
    time.sleep(0.5)
    pid = proc.pid
    COMPILEPID_FILE.write_text(str(pid))
    return request


def extract_tz(req: Request):
    timezones = [{"value": tz, "label": tz} for tz in pytz.all_timezones]
    qs = parse_qs(req.query_string)
    timezone = qs.get(b"timezone", str(config.my_timezone))
    if isinstance(timezone, list):
        timezone = timezone[0].decode("ascii")
    log.debug("timezone = %s", timezone)
    if timezone and (timezone not in pytz.all_timezones):
        log.error("Invalid timezone %s", timezone)
        raise ValueError("Invalid Timezone")
    return (timezone, pytz.timezone(timezone))


class IitFlask(Flask):
    def __init__(self, *args, **kwargs):
        super(IitFlask, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):

        # This is a guard against the werkzeig reloader
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            run_compile_job()
        return super(IitFlask, self).run(*args, **kwargs)


ICS_MIME = "text/calendar"

# where the magic happens!


def create_app(
    iit_config=None, config_filename=None, config_obj_path=None, project_name=None
):

    iit_config = iit_config or config

    # create the application
    app = IitFlask(__name__)

    # assign the callbacks
    app.after_request(run_compile_job)

    if config_filename:
        app.config.from_pyfile(config_filename)

    @app.route(STEPS[0], methods=[GET])
    @app.route(STEPS[1], methods=[GET])
    @app.route(STEPS[2], methods=[GET])
    @app.route(STEPS[3], methods=[GET])
    @app.route(STEPS[4], methods=[GET])
    def show_appointment_scheduler(
        block=None, year=None, month=None, day=None, _extra_conext=None
    ):

        (timezone, tzobj) = extract_tz(request)

        # Construct tzstring before anything else
        tzqs = ""
        if timezone:
            tzqs = f"?timezone={timezone}"

        choices = []

        # Fetch the choices, and make sure they're unique
        _values = set()
        selection = None
        for choice in fetch_more_human_choices(
            block,
            year,
            month,
            day,
            tzinfo=tzobj,
        ):
            # log.debug(choice)
            if choice["selection"] not in ("time",) and choice["value"] in _values:
                continue
            choices.append(choice)
            if choice["selection"] not in ("time",):
                _values.add(choice["value"])
            selection = choice["selection"]

        for (i, errlabel, sel) in (
            (block, "appointment", "block"),
            (year, "year", "year"),
            (month, "month", "month"),
            (day, "day", "day"),
        ):
            if (sel == selection) and i and (i not in _values):
                log.error(
                    "%s/%s (%s) not in %s", errlabel, choice["selection"], i, _values
                )
                abort(404, f"{i} is not a valid {errlabel}")

        now = arrow.utcnow()
        now = now.to(tzobj)
        now_year = now.year
        now_month = now.month

        choice_tpl = template_if_exists(BLOCK_CHOICE_TPL)

        # I know there's a shorter way to construct this,
        # but it can lead to getting confusing, so we'll do it the
        # long way for now.
        back_url = None
        back_label = None
        if block:
            # Previous: time block, current: year
            back_url = f"/{tzqs}"
            back_label = "Choose Appointment"
            choice_tpl = template_if_exists(YEAR_CHOICE_TPL)
        if year:
            # Previous: year, current: month
            back_url = f"/{block}/{tzqs}"
            back_label = f"Choose Year"
            choice_tpl = template_if_exists(MONTH_CHOICE_TPL)
        if month:
            # Previous: month, current: day
            back_url = f"/{block}/{year}/{tzqs}"
            back_label = f"Choose Month"
            choice_tpl = template_if_exists(DAY_CHOICE_TPL)
        if day:
            # Previous: day, current: time selection
            back_url = f"/{block}/{year}/{month}/{tzqs}"
            back_label = f"Choose Day"
        
        if back_url and (config.url_base) and not (back_url.startswith(config.url_base)):
            back_url = config.url_base + back_url


        month_name = None
        if month:
            month_name = list(MN)[month]
        

        context = {
            "timezones": [
                {
                    "value": t,
                    "label": t,
                }
                for t in pytz.all_timezones
            ],
            "choices": choices,
            "block": block,
            "choice_template": choice_tpl,
            "timezone": {
                "value": timezone,
                "label": timezone,
            },
            "year": year,
            "month": month,
            "month_name": month_name,
            "day": day,
            "meta": {
                "back": {
                    "url": back_url,
                    "label": back_label,
                }
            },
            "cfg": iit_config,
        }

        if _extra_conext:
            context.update(_extra_conext)

        # Next, the year.
        # if we don't have a block, render that
        return render_template(str(INDEX_TEMPLATE), **context)

    @app.route(STEPS[4], methods=[POST])
    def submit_complete(block, year=None, month=None, day=None):
        (timezone, tzobj) = extract_tz(request)
        # Once the form has been submitted
        # construct the ics as an attachment
        # email both the user and the "owners"
        time = request.form.get("time")
        email = request.form.get("email")
        name = request.form.get("name")
        details = request.form.get("details")

        context = {
            "cfg": iit_config or config,
            "has_errors": False,
            "errors": {},
            "timzeone": timezone,
        }

        if not time:
            add_error(context, "form_time", "null")
        if not name:
            add_error(context, "form_email", "null")
        if not email:
            add_error(context, "form_name", "null")

        if context["has_errors"]:
            return show_appointment_scheduler(block, year, month, day, context)

        (start_utc, end_utc) = time.split(";")
        tz = extract_tz(request)[1] or pytz.utc
        start = arrow.get(int(start_utc), tzinfo=tz)
        end = arrow.get(int(end_utc), tzinfo=tz)
        appt = iit_config.appointments.get(block)
        meeting_link = iit_config.MeetingGenClass().generate()
        req = AppointmentRequest(appt, start, end, email, name, details, meeting_link)
        req.send_emails()
        return render_template(str(CONFIRM_TEMPLATE), **context)

    return app
