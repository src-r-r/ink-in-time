import typing as T
import re
import logging

log = logging.getLogger(__name__)


class CallangParserError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{self.message}"

    def __repr__(self):
        return f"{type(self).__name__}: {self}"


class CallangTokenError(Exception):
    def __init__(self, token, message=None):
        self.token = token
        self.message = message

    def __str__(self):
        return f'{self.token}{self.message or ""}'

    def __repr__(self):
        return f"{type(self).__name__}: {self}"


class Tok:

    expr: re.Pattern = None

    @classmethod
    def match(cls, text):
        if not isinstance(cls, re.Pattern):
            raise TypeError(f"{cls.__name__}.expr is not a pattern")
        return cls.expr.match(text)

    def __init__(value):
        self.value = value


class Day(Tok):
    expr = re.compile(
        r"[(m(on)?)|(t(ue(s)?)?)|(w(ed)?)|(t(hu(rs)?)?)|(f(ri)?)?|(s(at)?)|(s(un)?)](day)?"
    )


class Comma(Tok):
    expr = re.compile(r"\,")


class Dash(Tok):
    expr = re.compile(r"\-")


TOKENS = [
    Day,
    Comma,
    Dash,
]


def get_match(tokval):
    for T in TOKENS:
        if T.match(text):
            return T(text)


def get_tokens(text):
    for tokval in re.compile("[\s]").split(text):
        match = get_match(tokval)
        if match:
            yield match
        else:
            raise ParseEr
