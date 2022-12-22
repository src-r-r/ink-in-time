import typing as T
from datetime import timedelta
from celery import Task

WORKFLOW_EVENTS = (
    WORKFLOW_INIT, WF_EVENT_START, WF_EVENT_END
)

class WorkflowEvent:
    INIT = "init"
    EV_START = "event_start"
    EV_END = "event_end"
    EVENTS = (
        INIT,
        EV_START,
        EV_END,
    )
    
    def __init__(self, event : T.AnyStr, delay : timedelta, task : T.Union[T.AnyStr, T.Task], **task_kwargs : T.Hashable[T.AnyStr, T.Any]):
        self.event = event
        self.delay = delay
        self.task = task
        self.task_kwargs = task_kwargs