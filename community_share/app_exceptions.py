class BadRequest(Exception):
    pass


class FileTypeNotImplemented(BadRequest):
    pass


class FileTypeNotPermitted(BadRequest):
    pass


class Forbidden(Exception):
    def __init__(self, message='Forbidden'):
        super().__init__(message)

class NotAuthorized(Exception):
    def __init__(self, message='You are not authorized to make this request'):
        super().__init__(message)

class NotFound(Exception):
    def __init__(self, message='Not found'):
        super().__init__(message)
