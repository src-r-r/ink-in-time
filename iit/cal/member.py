class Member:

    def __init__(self, email: T.AnyStr, cn : T.AnyStr=None, role : T.AnyStr=None):
        self.email = email
        self.cn = cn