#
# All extensions are defined here. They are initialized by Empty if
# required in your project's configuration. Check EXTENSIONS.
#

import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security
from flask_security import SQLAlchemyUserDatastore
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO
from flask_rq2 import RQ
from flask_static_compress import FlaskStaticCompress


toolbar = None

if os.environ['FLASK_ENV'] == 'development':
    # only works in development mode
    from flask_debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension()


db = SQLAlchemy()
migrate = Migrate(db=db)
ma = Marshmallow()
compress = FlaskStaticCompress()
io = SocketIO()
rq = RQ()
security = Security()


def security_init_kwargs():
    """
    **kwargs arguments passed down during security extension initialization by
    "empty" package.
    """
    from auth.models import User, Role

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    return dict(datastore=user_datastore)
