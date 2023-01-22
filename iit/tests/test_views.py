import typing as T
from flask.testing import Client
from werkzeug import Response

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