from datetime import datetime
from time import sleep
from .config import config
from .dc import compile_choices

def compile_available_times():
    """ Runs in the background to fetch the icals and generate blocks. """
    now = datetime.now()
    first_run=True
    sleep_time = config.db_compilation_interval
    while 1:
        if first_run:
            log.info("***(!)*** Compiling block choices for the first time. Please wait...")
        compile_choices()
        log.debug("Sleeping for %s", sleep_time)
        sleep(sleep_time)
        if first_run:
            log.info(":-) Done compiling block choices!")
            first_run=False