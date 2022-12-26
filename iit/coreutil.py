from pathlib import Path
import os

def first_config(*altpaths, filename : Path = "iit.yml", env_var="IIT_YML"):
    if os.environ.get(env_var):
        pth = Path(os.environ.get(env_var)).resolve()
        if not pth.exists():
            raise RuntimeError(f"{env_var} does not point to a file that exists")
        if not pth.is_file():
            raise RuntimeError(f"{env_var} does not point to a file")
        return pth
    for _dir in altpaths:
        pth = (Path(_dir) / Path(filename)).resolve()
        if pth.exists() and pth.is_file():
            return pth
    raise RuntimeError(f"Could not find `{filename}` in {altpaths}")