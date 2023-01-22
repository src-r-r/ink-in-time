from iit.controllers.block import find_available

def test_find_available(db_session, block_compiler, calendar_compiler):
    block = "Full Consultation"
    block_compiler.compile(db_session)
    calendar_compiler.compile(db_session)
    appts = find_available(db_session)
    assert appts == [block,]

    years = find_available(db_session, block=block)
    assert years == ["2023",]