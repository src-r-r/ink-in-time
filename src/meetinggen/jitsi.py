from .base import MeetingGenerator
from uuid import uuid1

class JitsiGenerator(MeetingGenerator):

    def generate(self):
        code = uuid1().hex
        return "https://meet.jit.si/{code}"