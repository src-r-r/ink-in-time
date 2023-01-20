import typing as T
from flask.testing import Client
from werkzeug import Response

from bs4 import BeautifulSoup
import arrow

def brew(resp : Response):
    return BeautifulSoup(resp.text)

def test_index(Session, client):
    resp = client.get('/')
    assert resp.status_code == 200
    soup = brew(resp)
    import ipdb; ipdb.set_trace()
