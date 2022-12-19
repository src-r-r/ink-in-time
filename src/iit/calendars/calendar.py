
class Calendar:
    def __init__(self, timezone: pytz.timezone):
        self.timezone = timezone
        self.events = list

    def sequence_end(self, event):
        return self._sequences[event["sequence"]]

    @property
    def start_date(self):
        return min(list(self.events.keys()))

    @property
    def end_date(self):
        return max(list(self.events.keys()))

    def _next_key(self, key):
        keys = list(self.events.keys())
        if key not in keys:
            return None
        next_i = keys.index(key) + 1
        if next_i >= len(keys):
            return None
        return keys[next_i]

    def add_event(self, vevent):
        start = vevent["dtstart"][0].value
        end = None
        sequence_event = None
        # If the event has an end date, set it.
        if "dtend" in vevent:
            end = vevent["dtend"][0].value
        # Otherwise, refer to the sequence
        elif "sequence":
            seq = vevent["sequence"][0].value
            if seq in self._sequences:
                sequence_event = self._sequences[seq]
        # If the squence has not been added, add it.
        if "sequence" in vevent:
            seq = vevent["sequence"][0].value
            if seq not in self._sequences:
                self._sequences[seq] = vevent
        # Assign the event to the start time.
        if start not in self.events:
            self.events[start] = []

        self.events[start].append(Event(self, start, end, sequence_event))

    def iter_all_events(self) -> T.Iterable[Event]:

        events = sorted(self.events.items(), key=lambda x: awareness(mkdt(x[0])))
        for e in events:
            yield e[1]

    def does_conflict(self, a_start, a_end):
        for eventset in self.iter_all_events():
            for event in eventset:
                if event.does_conflict(a_start, a_end):
                    return True
        return False