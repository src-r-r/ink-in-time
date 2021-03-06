from .iit_app import create_app
from .core import PROJ_ENV
from .config import project_name, config
from pathlib import Path
import os
import environ

env = environ.Env()

FLASK_DOTENV = env.bool("FLASK_DOTENV", False)

if FLASK_DOTENV:
    if Path(PROJ_ENV).exists():
        with PROJ_ENV.open() as f:
            env.read_env(f)

    # Or try loading from the execution path
    if Path(".env").exists():
        with Path(".env").open() as f:
            env.read_env(f)

app = create_app(project_name=project_name)

if __name__ == '__main__':

    _debug = env.bool("FLASK_DEBUG", False)
    app.debug = _debug
    # _debug = app.config.get('DEBUG', False)

    kwargs = {
        'host': os.getenv('FLASK_HOST', '0.0.0.0'),
        'port': int(os.getenv('FLASK_PORT', 5000)),
        'debug': _debug,
        'use_reloader': app.config.get('USE_RELOADER', _debug),
        **app.config.get('SERVER_OPTIONS', {})
    }

    from .extensions import SocketIO

    app.run(**kwargs)

    # SocketIO(app).run(app, **kwargs)
    
