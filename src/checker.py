from .config import config
import re
import socket
import pytz
from datetime import timedelta, time


def check_config():
    assert "grace_period" in config
    assert timedelta(**config["grace_period"])
    assert "time_span" in config
    assert timedelta(**config["time_span"])
    assert "workday" in config
    assert "start" in config["workday"]
    assert time(**config["workday"]["start"])
    assert "end" in config["workday"]
    assert time(**config["workday"]["end"])
    assert "timezone" in config
    assert pytz.timezone(config["timezone"])
    assert "calendars" in config
    for k in config["calendars"].keys():
        assert k in ("free", "blocked")
    assert "appointments" in config
    for (k, v) in config["appointments"].items():
        if "time" not in v:
            raise RuntimeError(f"Missing time for {k} appointment")
        if not (isinstance(v["time"], int) or re.match(r"^\d+$", time)):
            raise RuntimeError(f"appointments[{k}] (value={time}) is not a valid time")
    assert "email" in config
    assert "host" in config["email"]
    assert "port" in config["email"]
    assert "username" in config["email"]
    assert "password" in config["email"]
    print("Testing email connection:")
    s = socket.socket()
    s.connect((config["email"]["host"], config["email"]["port"]))
    print("[SUCCESS]")
    s.close()
