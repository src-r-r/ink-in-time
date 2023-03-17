import typing as T
from flask import (
    Flask,
    render_template as flask_render_template,
    request,
    abort,
    Request,
)
from urllib.parse import quote_plus, unquote_plus
from datetime import datetime, timedelta
from urllib.parse import parse_qs, parse_qsl
from werkzeug.serving import is_running_from_reloader
import time
import os
import atexit
from calendar import month_name as MN
import pytz
import celery
import arrow
import calendar
from multiprocessing import Process
from pathlib import Path
import logging


from celery import Celery
from environ import Env

from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy as SQLAlchemyExtension

from iit.config import get_config, DB_URL
from iit.models.database import db
from iit.tasks.task_loader import get_tasks
from iit.cal.event import OutboundEvent, InboundEvent
from iit.core.const import MOCK_ICS_DIR, FLASK_DEBUG, FLASK_ENV
from iit.controllers.block import find_block_options, find_available
from .email import (
    OrganizerAppointmentRequest as OAR,
    ParticipantAppointmentRequest as PAR,
)
from calendar import Calendar as PyCal
from sqlalchemy import create_engine
from jinja2 import Environment as JinjaEnv, PackageLoader, select_autoescape

env = Env()
Env.read_env(".env")

jinja_env = JinjaEnv(
    loader=PackageLoader("iit", "templates"),
    autoescape=select_autoescape(),
)

config = get_config()

BROKER_URL = env.url("BROKER_URL")

log = logging.getLogger(__name__)
APP_NAME = __name__

TPL_NS = Path("iit")
IDX_TPL = TPL_NS / "index"
INC_TPL = TPL_NS / "inc"
INDEX_TEMPLATE = IDX_TPL / "timeblock_selection.html"
CONFIRM_TEMPLATE = IDX_TPL / "confirmation.html"

CHOICE_TPL_DIR = TPL_NS / "choice"
BLOCK_CHOICE_TPL = CHOICE_TPL_DIR / "block.html"
YEAR_CHOICE_TPL = CHOICE_TPL_DIR / "year.html"
MONTH_CHOICE_TPL = CHOICE_TPL_DIR / "month.html"
DAY_CHOICE_TPL = CHOICE_TPL_DIR / "day.html"
WEEK_CHOICE_TPL = CHOICE_TPL_DIR / "week.html"
TIME_CHOICE_TPL = CHOICE_TPL_DIR / "time.html"

CHOICE_DT_FORMAT = "%H:%M %p - %H:%M %p, %Z"


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


def extract_tz(req: Request):
    timezones = [{"value": tz, "label": tz} for tz in pytz.all_timezones]
    arg_timezone = request.args.get("timezone")
    if arg_timezone:
        arg_timezone = unquote_plus(arg_timezone)
    my_timezone = config.get("scheduling", {}).get("my_timezone", None)
    return arg_timezone or my_timezone or "UTC"


ICS_MIME = "text/calendar"

APP_NAME = __name__


def render_template(pth: T.Union[Path, T.AnyStr], *args, **kwargs):
    """Adds a couple of fixes to "render_template" to make it easier."""
    # log.debug("Rendering template %s with kwargs=%s", str(pth), kwargs)
    return flask_render_template(str(pth), *args, **kwargs)


def group_to(lst: T.Iterable, sz: int):
    return [lst[n : n + sz] for n in range(0, len(lst), sz)]


def time_choice_value(tzrange: T.Tuple[datetime]):
    (start, end) = tzrange
    duration = (end - start).minutes
    return f"{start.toordinal()},{end.toordinal()},{duration}"


def time_choice_label(tzrange: T.Tuple[datetime]):
    (start, end) = tzrange
    duration = (end - start).minutes
    return f"{start.toordinal()},{end.toordinal()},{duration}"


# where the magic happens!
def create_app(
    iit_config=None,
    config_filename=None,
    config_obj_path=None,
    project_name=None,
    db_url=DB_URL,
):

    iit_config = iit_config or config

    celery_app = Celery("inkintime", broker=BROKER_URL)

    app = Flask(APP_NAME)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url

    # Add custom filters to the jinja environment
    app.jinja_env.filters["month_name"] = calendar.month_name.__getitem__
    app.jinja_env.filters["day_name"] = calendar.day_name.__getitem__
    app.jinja_env.filters["enumerate"] = lambda x: enumerate(x)

    # app.jinja.env.filters["now_year"] = lambda x : datetime().now().year
    # app.jinja.env.filters["now_month"] = lambda x : datetime().now().month
    # app.jinja.env.filters["now_day"] = lambda x : datetime().now().day

    db.init_app(app)

    with app.app_context():
        from iit.models.block import Block

        db.create_all()
        db.session.commit()

    app.config["url_base"] = iit_config["site"]["url_base"]
    app.debug = FLASK_DEBUG
    app.debug = FLASK_ENV.lower() == "debug"

    engine = create_engine(DB_URL)

    if config_filename:
        app.config.from_pyfile(config_filename)

    @app.context_processor
    def add_globals():
        return {
            "config": config,
            "all_timezones": [
                {"value": quote_plus(tz), "label": tz.replace("_", " ")}
                for tz in pytz.all_timezones
            ],
        }

    @app.route("/", methods=["GET"])
    def get_time_blocks():
        blocks = find_available(db.session)
        return render_template(
            BLOCK_CHOICE_TPL, block_choices=blocks, timezone=extract_tz(request)
        )

    @app.route("/<block>", methods=["GET"])
    def get_year(block: T.AnyStr):
        year_choices = find_available(db.session, block=block)
        year_choices = [int(y[0]) for y in year_choices]
        return render_template(
            YEAR_CHOICE_TPL,
            block_choice=block,
            year_choices=year_choices,
            timezone=extract_tz(request),
        )

    @app.route("/<block>/<int:year>", methods=["GET"])
    def get_month(block: T.AnyStr, year: int):
        avail = find_available(db.session, block=block, year=year)
        context = {
            "block": block,
            "year": year,
            "month_choices": [int(i[0]) for i in avail],
            "timezone": extract_tz(request),
        }
        return render_template(MONTH_CHOICE_TPL, **context)

    @app.route("/<block>/<int:year>/<int:month>", methods=["GET"])
    def get_day(block: T.AnyStr, year: int, month: int):
        q = request.args.to_dict()
        week = q.get("week", None)
        current_dom = datetime.now().day
        days_of_month = [
            int(i[0])
            for i in find_available(db.session, block=block, year=year, month=month)
        ]
        pycal = PyCal()
        caldays = [d for d in pycal.itermonthdays4(year, month)]
        day_choices = [
            {
                "dom": dom,
                "dow": dow,
                "enabled": dom in days_of_month and dom >= current_dom,
                "today": dom == current_dom,
            }
            for (year, month, dom, dow) in caldays
        ]
        n_weeks = int(len(caldays) / 7)
        week_choices = [i for i in range(1, n_weeks + 1)]
        try:
            if week:
                week = int(week)
                if week not in week_choices:
                    raise ValueError()
        except ValueError as ve:
            raise ValueError(
                f"Invalid week: {week}, must be a week number {week_choices}"
            )
        context = {
            "block": block,
            "year": year,
            "month": month,
            "day_choices": day_choices,
            "timezone": extract_tz(request),
        }
        return render_template(DAY_CHOICE_TPL, **context)

    @app.route("/<block>/<int:year>/<int:month>/<int:day>", methods=["GET", "POST"])
    def pick_a_time(block: T.AnyStr, year: int, month: int, day: int):
        context = {
            "block": block,
            "year": year,
            "month": month,
            "day": day,
            "time_choices": find_available(
                db.session, block=block, year=year, month=month, day=day
            ),
            "timezone": extract_tz(request),
        }
        if request.method == "GET":
            return render_template(TIME_CHOICE_TPL, **context)
        # if POST...

        for task in get_tasks(config, ["init"]):
            task.apply_async(event=OutboundEvent.from_post_data(start))
        return render_template(CONFIRM_TEMPLATE)

    return app
