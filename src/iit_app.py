from flask import Flask, render_template, request, abort
from datetime import datetime, timedelta
from urllib.parse import parse_qs, parse_qsl
from calendar import month_name as MN
import pytz
import arrow
from .config import config
from .checker import check_config
from .db import fetch_more_human_choices
from .calendar import calblock_choices
import logging
log = logging.getLogger(__name__)

def create_app(config_filename=None):
   # create a minimal app
   app = Flask(__name__)
   if config_filename:
      app.config.from_pyfile(config_filename)

   
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

      appts = config.appointments

      # Figure out timezones
      
      timezones = [{"value" : tz, "label": tz} for tz in pytz.all_timezones]
      qs = parse_qs(request.query_string)
      timezone = qs.get(b"timezone", str(config.my_timezone))
      if isinstance(timezone, list):
         timezone = timezone[0].decode("ascii")
      log.debug("timezone = %s", timezone)
      if timezone and (timezone not in pytz.all_timezones):
         log.error("Invalid timezone %s", timezone)
         # log.info("Valid timezones: %s", pytz.all_timezones)
         abort(400)
      tzobj = pytz.timezone(timezone)

      # if we don't have a block, render that
      if not block:
         context = {
               "choices": [
                  {"value": k, "label": a.label, "time": a.time}
                  for (k, a) in appts.items()
               ],
               "timezones": timezones,
               "timezone": {
                  "value": timezone,
                  "label": timezone,
               },
         }
         return render_template(TEMPLATE, **context)
      else:
         # or check it
         if block not in appts:
               abort(Response(f"Block {block} not found"))

      now = arrow.utcnow()
      now = now.to(tzobj)
      now_year = now.year
      now_month = now.month

      appt = appts[block]
      duration = appt.time
      _values = []
      choices = []
      for choice in fetch_more_human_choices(block, year, month, day, tzinfo=tzobj):
         if choice["value"] in _values:
               continue
         choices.append(choice)
         _values.append(choice["value"])

      # construct meta info

      # I know there's a shorter way to construct this,
      # but it can lead to getting confusing, so we'll do it the
      # long way for now.
      tzqs = ""
      if timezone:
         tzqs=f"?timezone={timezone}"
      if block:
         back_url = f"/{tzqs}"
         back_label = "Choose Time Block"
      if year:
         back_url = f"/{block}/{tzqs}"
         back_label = f"Choose Year"
      if month:
         back_url = f"/{block}/{year}/{tzqs}"
         back_label = f"Choose Month"
      if day:
         back_url = f"/{block}/{year}/{month}/{tzqs}"
         back_label = f"Choose Day"
      
      month_name=None
      if month:
         month_name = list(MN)[month]

      # Next, the year.
      # if we don't have a block, render that
      return render_template(TEMPLATE, **{
         "timezones": [(t, t) for t in pytz.all_timezones],
         "choices": choices,
         "block": block,
         "timezone": {
               "value": timezone,
               "label": timezone,
         },
         "timezones": timezones,
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
      })


   @app.route(STEPS[4], methods=[POST])
   def submit_complete(block, year=None, month=None, day=None):
      # Once the form has been submitted
      # construct the ics as an attachment
      # email both the user and the "owners"
      time = request.form.get("time")
      email = request.form.get("email")
      details = request.form.get("details")
   
   return app