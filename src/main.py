from flask import Flask, request
from .config import config
from .checker import check_config
import logging.config
import logging

log = logging.getLogger(__name__)
app = Flask(__name__)

STEPS = [
    "/",
    "/<string:block>",
    "/<string:block>/<int:year>",
    "/<string:block>/<int:year>/<int:month>",
    "/<string:block>/<int:year>/<int:month>/<int:day>",
]
GET = "GET"


@app.route(STEPS[0], methods=[GET])
@app.route(STEPS[1], methods=[GET])
@app.route(STEPS[2], methods=[GET])
@app.route(STEPS[3], methods=[GET])
@app.route(STEPS[4], methods=[GET])
def show_form(block, year=None, month=None, day=None):
    pass


@app.route(STEPS[4], methods=[GET])
def submit_complete(block, year=None, month=None, day=None):
    request.form


if __name__ == "__main__":
    check_config()
    logging.config.dictConfig(config["logging"])
    # app.run(debug=True)
