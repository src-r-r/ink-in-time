import re
import socket
import pytz
import humanize
from datetime import timedelta, time
import importlib

def check_config(config):
    from .core import IS_EMAIL
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

    assert IS_EMAIL(config["organizer"]["email"])

    # Email
    assert "email" in config
    assert "meeting_link_generator" in config["email"]
    cls = config["email"]["meeting_link_generator"]
    module_name, class_name = cls.split(":", 1)
    _mod = importlib.import_module(module_name)
    MeetingGenClass = getattr(_mod, class_name)
    assert MeetingGenClass is not None
    assert hasattr(MeetingGenClass, "generate")
    assert callable(MeetingGenClass.generate)
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
    try:
        s = socket.socket()
        s.connect((e["host"], e["port"]))
        print("[SUCCESS]")
        s.close()
    except ConnectionRefusedError as exc:
        nocreds = dict([(k, v) for (k, v) in e.items() if k not in ("username, password")])
        raise RuntimeError(f"Could not connect to {nocreds}: {exc}")

