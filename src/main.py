from flask import Flask, request, render_template, abort
from .config import config, get_appts
from .checker import check_config
from urllib.parse import parse_qs, parse_qsl
from .calendar import calblock_choices
from datetime import timedelta
import jinja2
import logging.config
import logging
import pytz

log = logging.getLogger(__name__)
app = Flask(__name__)

STEPS = [
    "/",
    "/<string:block>/",
    "/<string:block>/<int:year>/",
    "/<string:block>/<int:year>/<int:month>/",
    "/<string:block>/<int:year>/<int:month>/<int:day>/",
]
GET = "GET"
POST = "POST"


@app.route(STEPS[0], methods=[GET])
@app.route(STEPS[1], methods=[GET])
@app.route(STEPS[2], methods=[GET])
@app.route(STEPS[3], methods=[GET])
@app.route(STEPS[4], methods=[GET])
def show_appointment_scheduler(block=None, year=None, month=None, day=None):
    # TODO: sanity checking of timespan; user might
    #       be able to specify time outside of workday!!!

    TEMPLATE = "index/timeblock_selection.html"

    appts = get_appts()

    # if we don't have a block, render that
    if not block:
        return render_template(TEMPLATE, **{
            "choices": [
                {"value": k, "label": a["label"], "time": a["time"]}
                for (k, a) in appts.items()
            ],
        })
    else:
        # or check it
        if block not in appts:
            abort(Response(f"Block {block} not found"))


    appt = appts[block]
    duration = timedelta(minutes=appt["time"])
    choices = calblock_choices(duration, year, month, day)

    # construct meta info

    # I know there's a shorter way to construct this,
    # but it can lead to getting confusing, so we'll do it the
    # long way for now.
    if block:
        back_url = "/"
        back_label = "Choose Time Block"
    if year:
        back_url = f"/{block}"
        back_label = f"Choose Time Block"
    if month:
        back_url = f"/{block}/{year}"
        back_label = f"Choose Year"
    if day:
        back_url = f"/{block}/{year}/{month}/"
        back_label = f"Choose Month"

    # Next, the year.
    # if we don't have a block, render that
    return render_template(TEMPLATE, **{
        "timezones": [(t, t) for t in pytz.all_timezones],
        "choices": choices,
        "year": year,
        "month": month,
        "day": day,
        "meta": {
            "back": {
                "url": back_url,
                "label": back_label,
            }
        },
    })


@app.route(STEPS[4], methods=[POST])
def submit_complete(block, year=None, month=None, day=None):
    # Once the form has been submitted
    # construct the ics as an attachment
    # email both the user and the "owners"
    time = request.form.get("time")
    email = request.form.get("email")
    details = request.form.get("details")


if __name__ == "__main__":
    check_config()
    logging.config.dictConfig(config["logging"])
    app.run(debug=True)
