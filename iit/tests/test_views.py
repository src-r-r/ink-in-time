import typing as T
from flask.testing import Client
from werkzeug import Response
from calendar import month_name, weekday, day_name

from bs4 import BeautifulSoup
import arrow

def brew(resp : Response):
    return BeautifulSoup(resp.text)

def test_index(db_session, block_compiler, calendar_compiler, client):
    block_compiler.compile(db_session)
    calendar_compiler.compile(db_session)
    resp = client.get('/')
    assert resp.status_code == 200
    soup = brew(resp)
    assert "Full Consultation" in resp.text

def test_year(db_session, block_compiler, calendar_compiler, client):
    block_compiler.compile(db_session)
    calendar_compiler.compile(db_session)
    resp = client.get('/Full%20Consultation')
    assert resp.status_code == 200
    soup = brew(resp)
    curr_year = block_compiler.start.date().year
    assert str(curr_year) in resp.text

def test_month(db_session, block_compiler, calendar_compiler, client):
    curr_year = block_compiler.start.date().year
    curr_month = block_compiler.start.date().month
    block_compiler.compile(db_session)
    calendar_compiler.compile(db_session)
    resp = client.get(f'/Full%20Consultation/{curr_year}')
    assert resp.status_code == 200
    soup = brew(resp)
    assert str(month_name[curr_month]) in resp.text

def test_day(db_session, block_compiler, calendar_compiler, client):
    curr_year = block_compiler.start.date().year
    curr_month = block_compiler.start.date().month
    curr_day = block_compiler.start.date().day
    curr_weekday = weekday(curr_year, curr_month, curr_day)
    curr_weekday_name = day_name[curr_weekday]

    block_compiler.compile(db_session)
    calendar_compiler.compile(db_session)
    resp = client.get(f'/Full%20Consultation/{curr_year}/{curr_month}')
    assert resp.status_code == 200
    soup = brew(resp)
    assert str(curr_day) in resp.text
    assert str(curr_weekday_name) in resp.text

def test_get_time(db_session, block_compiler, calendar_compiler, client):
    curr_year = block_compiler.start.date().year
    curr_month = block_compiler.start.date().month
    curr_day = block_compiler.start.date().day
    # curr_weekday = weekday(curr_year, curr_month, curr_day)
    # curr_weekday_name = day_name[curr_weekday]

    block_compiler.compile(db_session)
    calendar_compiler.compile(db_session)
    resp = client.get(f'/Full%20Consultation/{curr_year}/{curr_month}/{curr_day}')
    assert resp.status_code == 200
    soup = brew(resp)