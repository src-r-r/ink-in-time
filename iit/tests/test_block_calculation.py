from iit.cal.block.compiler import PostgresBlockCompiler
from datetime import timedelta
import arrow

def test_block_compiler():
    start = arrow.now().ceil("hour")
    end = start.shift(days=1)
    duration = timedelta(minutes=30)
    duration_label = "30min"
    comp = PostgresBlockCompiler(engine, start, end, duration, duration_label)