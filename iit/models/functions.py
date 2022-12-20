from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.types import Integer, TIMESTAMP
class extract(GenericFunction):
    type = Integer
    inherit_cache = True


# Range functions 
# https://www.postgresql.org/docs/current/functions-range.html
class lower(GenericFunction):
    type = TIMESTAMP
    inherit_cache = True

class upper(GenericFunction):
    type = TIMESTAMP
    inherit_cache = True
    synchronize_session = False