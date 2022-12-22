import typing as T
from celery import Task
import logging


log = logging.getLogger(__name__)

class SendParticipantInvitation(Task):
    
    def __init__(self, *args, **kwargs):
        super(SendEmailInvite, self).__init__()
    
    def run(self):
        pass

class SendHostInvitation(Task):
    
    def __init__(self, *args, **kwargs):
        super(SendHostInvitation, self).__init__()
    
    def run(self):
        pass