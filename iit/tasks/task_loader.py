import typing as T
from celery import Task
from importlib import import_module

def get_tasks(config : T.Hashable, events=None) -> T.Iterator[Task]:
    for task_data in config["tasks"]:
        if events and config["event"] not in events:
            continue
        (_modname, _classname) = task_data["task"].rsplit(".")
        _task_kwargs : T.Hashable = task_data.get("kwargs", {})
        module = import_module(_modname)
        _TaskClass : T.ClassVar[Task] = getattr(module, _classname)
        yield _TaskClass(**task_kwargs)