from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData
from sqlalchemy.dialects.postgresql import TSTZRANGE

meta = MetaData()

block = Table(
    "block", meta,
    Column("id", Integer, primary_key=True),
    Column("name", String(512)),
    Column("during", TSTZRANGE()),
    Column("is_unavailable", Boolean, nullable=True),
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    block.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    block.drop()
