import re
import socket
import pytz
from datetime import timedelta, time

def check_config(config):
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
    assert "database" in config
    assert "path" in config["database"]
    assert "compilation_interval" in config["database"]
    assert timedelta(**config["database"]["compilation_interval"])
    assert "calendars" in config
    assert "email" in config
    assert "outbound" in config["email"]

    e = config["email"]["outbound"]
    print("Testing email connection:")
    s = socket.socket()
    s.connect((e["host"], e["port"]))
    print("[SUCCESS]")
    s.close()
