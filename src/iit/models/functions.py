from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.types import Integer
class extract(GenericFunction):
    type = Integer
    inherit_cache = True
