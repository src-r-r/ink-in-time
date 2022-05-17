import re
import socket
import pytz
import humanize
from datetime import timedelta, time

def check_config(config):
    # Scheduling
    assert "scheduling" in config
    assert "my_timezone" in config["scheduling"]
    assert config["scheduling"]["my_timezone"] in pytz.all_timezones
    assert "appointments" in config["scheduling"]
    assert "grace_period" in config["scheduling"]
    assert timedelta(**config["scheduling"]["grace_period"])
    assert "workday" in config["scheduling"]
    assert "start" in config["scheduling"]["workday"]
    assert "end" in config["scheduling"]["workday"]
    assert time(**config["scheduling"]["workday"]["start"])
    assert time(**config["scheduling"]["workday"]["end"])
    assert "view_duration" in config["scheduling"]
    assert timedelta(**config["scheduling"]["view_duration"])

    # database
    assert "database" in config
    assert "path" in config["database"]
    assert "compilation_interval" in config["database"]
    assert timedelta(**config["database"]["compilation_interval"])
    assert "calendars" in config

    assert "organizer" in config
    assert "cn" in config["organizer"]
    assert "email" in config["organizer"]

    # Email
    assert "email" in config
    assert "server" in config["email"]
    assert "organizer" in config["email"]
    assert "subject" in config["email"]["organizer"]
    assert "participant" in config["email"]
    assert "subject" in config["email"]["participant"]

    # ics
    assert "ics" in config
    assert "summary" in config["ics"]

    assert "dt_format" in config["ics"]
    ics = config["ics"]
    assert "start" in ics["dt_format"]
    assert "end" in ics["dt_format"]

    if "humanize_function" in ics:
        assert hasattr(humanize, ics["humanize_function"])
    

    # Site settings
    if "site" in config:
        if "backref" in config["site"]:
            assert "url" in config["site"]["backref"]
            assert "label" in config["site"]["backref"]

    e = config["email"]["server"]
    print("Testing email connection:")
    s = socket.socket()
    s.connect((e["host"], e["port"]))
    print("[SUCCESS]")
    s.close()
