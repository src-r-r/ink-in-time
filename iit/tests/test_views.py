<<<<<<< HEAD
import typing as T
from flask.testing import Client
from werkzeug import Response

from bs4 import BeautifulSoup
import arrow

def test_shows_years(Session, remote_compiled_calendar, client : Client):
    now = arrow.now()
    resp : Response = client.get("/")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data)
    import ipdb; ipdb.set_trace()
    assert now.datetime.year in resp.data
=======

def test_index(compiled_blocks, client):
    resp = client.get('/')
    import ipdb; ipdb.set_trace()
    assert resp.status_code == 200
>>>>>>> 8e326f1 (fix some context and view issues.)
