import typing as T

def extract(s: T.AnyStr, sep: T.AnyStr, size: int, default=None, ext_as=None):
    ext_as = ext_as or str
    parts = s.split(sep)
    return [
        ext_as(s)
        for s in tuple(parts + [default for i in range(0, max(size - len(parts), 0))])
    ]