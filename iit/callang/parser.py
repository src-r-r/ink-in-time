import typing as T
import re
import logging
import arrow
from datetime import time
from iit.callang.util import extract
from simple_chalk import chalk, yellow, blue, green, red, magenta

log = logging.getLogger(__name__)


class CallangParserError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{self.message}"

    def __repr__(self):
        return f"{type(self).__name__}: {self}"


class CallangTokenError(Exception):
    def __init__(self, token, i=0, message=None):
        self.token = token
        self.i = i
        self.message = message

    def __str__(self):
        s = f"{self.token}"
        if self.i:
            s += f" at character {self.i}"
        if self.message:
            s += f": {self.message}"
        return s

    def __repr__(self):
        return f"{type(self).__name__}: {self}"


class CallangInterpreterError(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return f'{self.message or ""}'

    def __repr__(self):
        return f"{type(self).__name__}: {self}"


class Tok:

    expr: re.Pattern = None

    @classmethod
    def match(cls, text):
        expr = getattr(cls, "expr")
        if not isinstance(expr, re.Pattern):
            raise TypeError(f"{cls.__name__}.expr ({expr}) is not a pattern")
        return expr.match(text)

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"({self.__class__.__name__}: '{self.value}')"

    def __repr__(self):
        return f"{self}"

    def __eq__(self, o):
        return type(o) == type(self) and o.value == self.value


SUNDAY = "sunday"
MONDAY = "monday"
TUESDAY = "tuesday"
WEDNESDAY = "wednesday"
THURSDAY = "thursday"
FRIDAY = "friday"
SATURDAY = "saturday"

DAY_EQUIV = [
    (MONDAY, "mon", "mo", "m"),
    (TUESDAY, "tue", "tu", "t"),
    (WEDNESDAY, "wed", "we", "w"),
    (THURSDAY, "thu", "th", "h"),
    (FRIDAY, "fri", "fr", "f"),
    (SATURDAY, "sat", "sa", "a"),
    (SUNDAY, "sun", "su", "s"),
]

DAYS_ORDER = [d[0] for d in DAY_EQUIV]


class Single(Tok):
    pass


class Range(list):
    pass


class Day(Single):
    expr = re.compile("|".join(["|".join(line) for line in DAY_EQUIV]))

    @property
    def _norm_name(self):
        return [d[0] for d in DAY_EQUIV if self.value.lower() in d][0]

    def normalize(self):
        return Day(self._norm_name)

    @property
    def _i(self):
        return DAYS_ORDER.index(self._norm_name)

    def __cmp__(self, other):
        return self._i - other._i

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0


class Range(list):
    def __init__(self, start: Single, end: Single):
        self.start = start
        self.end = end

    def check(self):
        if self.start > self.end:
            raise CallangInterpreterError(
                f"Start ({start}) is greater than end ({end})"
            )

    def normalize(self):
        raise NotImplementedError()

    @classmethod
    def _from_single(cls, sing):
        inst = cls(sing, sing)
        inst.start = sing
        inst.end = None
        return inst


class Comma(Tok):
    expr = re.compile(r"\,")


class Dash(Tok):
    expr = re.compile(r"-")


class TimeVal(Single):
    expr = re.compile(r"\d+(:\d+(:\d+)?)?")

    def __init__(self, value, _is_pm=False):
        super(TimeVal, self).__init__(value)
        self.is_pm = _is_pm

    def _as_time(self):
        if isinstance(self.value, time):
            return self.value
        parts = self.value.split(":")
        (hour, minute, second) = extract(self.value, ":", 3, 0, int)
        if self.is_pm and hour < 12:
            hour += 12
        return time(hour, minute, second)

    def normalize(self):
        return TimeVal(self._as_time())

    def __gt__(self, o):
        return self._as_time() > o._as_time()

    def __lt__(self, o):
        return self._as_time() < o._as_time()

    def __eq__(self, o):
        if not isinstance(o, type(self)):
            return False
        return self._as_time() == o._as_time()

    def __str__(self):
        return f"{self._as_time()}"


class Merid(Tok):
    expr = re.compile(r"[ap]\.?m?\.?", re.I)

    @property
    def is_pm(self):
        return self.value[0].lower() == "p"


class DayRange(Range):
    def normalize(self):
        sing = self.start.normalize()
        while sing != self.end.normalize():
            log.debug("normalize %s, yield %s", self, sing)
            yield sing
            sing = Day(DAYS_ORDER[sing._i + 1])
        log.debug("normalize %s, yield %s", self, sing)
        yield sing


class TimeRange(Range):
    def __init__(self, start: TimeVal, end: TimeVal):
        # The user may not have specify am/pm for times.
        # In that case, infer based on hour order.
        stime = start._as_time()
        etime = end._as_time()
        super(TimeRange, self).__init__(start, end)

    def normalize(self):
        start = self.start.normalize()
        end = self.end.normalize()
        sing = TimeRange(start, end)
        log.debug("normalize %s, yield %s", self, sing)
        yield sing

    def __str__(self):
        return f"{self.start} - {self.end}"

    def __repr__(self):
        return f"<{type(self).__name__} {self}>"


TOKENS = [
    Day,
    Comma,
    Dash,
    TimeVal,
    Merid,
    Comma,
    Dash,
]


class TokenReached(Exception):
    pass


class TokenizerBase:
    def __init__(self):
        self.stack = []
        self._iter: T.Iterator[T.AnyStr] = None
        self._i = None

    def get_match(self, tokval):
        for T in self.Meta.TOKENS:
            if T.match(tokval):
                return T(tokval)

    def on_char(self, i: int, c: T.AnyStr):
        log.debug("[%d] (%s) - %s", i, c, yellow(self._stk))
        if re.match(r"[\s\t]", c):
            log.debug("whitespace '%s'", c)
            if self.stack:
                yield self.get_match(self._stk)
            self.stack = []
        # (number) followed by (word) (e.g. "4PM")
        elif re.match(r"[a-zA-Z]", c) and re.match(r"\d+", self._stk):
            tokval = self._stk
            self.stack = [c]
            yield self.get_match(tokval)
        # Symbols
        elif re.match(r"[\-\,]", c):
            if self._stk:
                yield self.get_match(self._stk)
                self.stack = []
            yield self.get_match(c)
        # Time
        elif re.match(r"\:", c) and re.match(r"(\d+(\:\d+)?)", self._stk):
            self.stack.append(c)
        # General number
        elif re.match(r"[0-9]+", c):
            log.debug("number: %s", c)
            self.stack.append(c)
        # any character
        elif re.match(r"[a-zA-Z]", c):
            self.stack.append(c)
        # This is an error
        else:
            raise CallangTokenError(c, i, "Invalid token")

    @property
    def _stk(self):
        return "".join(self.stack)

    def _next(self):
        return next(self._iter)

    def iter_tokens(self, text):
        log.debug(
            "Incoming text: %s, %s", blue(f"({len(text)} characters)"), magenta(text)
        )
        titer = iter(text)
        self.stack = []
        i = 0
        while 1:
            try:
                c = next(titer)
                for tok in self.on_char(i, c):
                    log.debug("**yielding %s", tok)
                    yield tok
                i += 1
            except StopIteration:
                last = self.get_match(self._stk)
                yield last
                log.debug("tokenizing %s complete", magenta(text))
                return

    class Meta:
        TOKENS = None


class DayListTokenizer(TokenizerBase):
    class Meta:
        TOKENS = [
            Day,
            Dash,
            Comma,
        ]


class TimeListTokenizer(TokenizerBase):
    class Meta:
        TOKENS = [
            TimeVal,
            Dash,
            Comma,
            Merid,
        ]


class SingleAndRangeList(list):
    def _get_types(self):
        return (Single, Range)

    def __init__(self, *items):
        super(SingleAndRangeList, self).__init__()
        for i in items:
            if not isinstance(i, self._get_types()):
                raise CallangInterpreterError(
                    f"{i} cannot be added to a SingleAndRangeList"
                )
            self.append(i)

    def _normalized(self):
        for i in self:
            if isinstance(i, Single):
                log.debug("normalize %s, yield %s", self, i)
                yield i.normalize()
            if isinstance(i, Range):
                for j in i.normalize():
                    log.debug("normalize %s.%s, yield %s", self, i, j)
                    yield j

    def normalized(self):
        return type(self)(*[i for i in self._normalized()])


class DayList(SingleAndRangeList):
    pass


class TimeList(SingleAndRangeList):
    pass


class ListOrRangeParser:
    def __init__(self):
        self.stack: T.List[T.Any] = []
        self._iter: T.Iterator = None

    def parse_token(self, tok):
        raise NotImplementedError()

    def _next(self):
        if not self._iter:
            return None
        return next(self._iter)

    def as_list(self):
        ListClass = self.Meta.LIST_CLASS
        return ListClass(*self.stack)

    def parse(self, text: T.AnyStr):
        Tokenizer = self.Meta.TOKENIZER_CLASS
        tokenizer = Tokenizer()
        self.stack = []
        self._iter = tokenizer.iter_tokens(text)
        log.debug("-- start iter over tokens --")
        while 1:
            try:
                tok = next(self._iter)
                self.parse_token(tok)
            except StopIteration:
                log.debug("-- parsing iter over tokens complete --")
                return self.as_list()

    class Meta:
        TOKENIZER_CLASS = None
        LIST_CLASS = None


class DayListParser(ListOrRangeParser):
    def parse_token(self, tok):
        if isinstance(tok, Day):
            log.debug("encountered: %s, push", tok)
            self.stack.append(tok)
            log.debug(yellow("stack: %s"), self.stack)
            return True
        if isinstance(tok, Dash):
            start = self.stack.pop()
            end = self._next()
            log.debug("encountered: %s, fetch %s to add to %s", tok, end, start)
            day_range = DayRange(start, end)
            day_range.check()
            self.stack.append(day_range)
            log.debug(yellow("stack: %s"), self.stack)

            return True
        return True

    class Meta:
        TOKENIZER_CLASS = DayListTokenizer
        LIST_CLASS = DayList


class TimeListParser(ListOrRangeParser):
    def __init__(self, *args, **kwargs):
        # This is a work-around so that we don't have
        # to consume the last token.
        self._range_context = dict()
        super(TimeListParser, self).__init__(*args, **kwargs)

    def parse_token(self, tok):
        if isinstance(tok, TimeVal):
            log.debug("encountered: %s, push", tok)
            if self._range_context:
                log.debug("range context, so converting to TimeRange")
                start = self._range_context["start"]
                end = tok
                tok = TimeRange(start, end)
                self._range_context = dict()
            self.stack.append(tok)
            return False
        if isinstance(tok, Merid):
            timeval = self.stack.pop()
            # Whenever the parser encounters a TimeRange, it first constructs the
            # time range without looking for a Merid. In this case we must
            # extract the end time, and make that a PM.
            if isinstance(timeval, TimeVal):
                log.debug("Setting %s.is_pm = %s", timeval, tok.is_pm)
                timeval.is_pm = tok.is_pm
            elif isinstance(timeval, TimeRange):
                log.debug("Setting %s.is_pm = %s", timeval, tok.is_pm)
                timeval.end.is_pm = tok.is_pm
                timeval.check()
            self.stack.append(timeval)
            log.debug(yellow("stack: %s"), self.stack)
            return True
        if isinstance(tok, Dash):
            timeval = self.stack.pop()
            end = None
            self._range_context.update({"start": timeval, "end": None})
            log.debug(yellow("stack: %s"), self.stack)
            return True
        return True

    class Meta:
        TOKENIZER_CLASS = TimeListTokenizer
        LIST_CLASS = TimeList
