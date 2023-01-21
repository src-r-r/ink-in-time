import typing as T
from flask.testing import Client
from werkzeug import Response

from bs4 import BeautifulSoup
import arrow

def brew(resp : Response):
    return BeautifulSoup(resp.text)

def test_index(remote_compiled_calendar, db_session, client):
    resp = client.get('/')
    assert resp.status_code == 200
    soup = brew(resp)
    assert "Full Consultation" in resp.text