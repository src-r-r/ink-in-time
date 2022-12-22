import typing as T
from importlib import import_module
from iit.cal.source.remote import RemoteCalendarSource, CalendarSource


def get_sources(config: T.Hashable) -> T.Iterator[CalendarSource]:
    sources_specs = config["calendars"]["blocked"]
    for source_spec in sources_specs:
        if isinstance(source_spec, str):
            yield RemoteCalendarSource(source_spec)
            continue
        (_modname, _classname) = str(source_spec["class"]).rsplit(".")
        source_kwargs : T.Hashable[T.Any] = source_spec.get("kwargs", {})
        source_args : T.Iterable[T.Any] = source_spec.get("args", [])
        _mod = import_module(_modname)
        _CalendarSource: T.ClassVar[CalendarSource] = getattr(_mod, _classname)
        return _CalendarSource(*source_args, **source_kwargs)