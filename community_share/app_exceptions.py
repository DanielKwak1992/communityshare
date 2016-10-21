class BadRequest(Exception):
    pass


class FileTypeNotImplemented(BadRequest):
    pass


class FileTypeNotPermitted(BadRequest):
    pass


class Unauthorized(Exception):
    def __init__(self, message='Authorization failed'):
        super().__init__(message)


class Forbidden(Exception):
    def __init__(self, message='Forbidden'):
        super().__init__(message)


class NotFound(Exception):
    def __init__(self, message='Not found'):
        super().__init__(message)


class ServerError(Exception):
    def __init__(self, message='Server error'):
        super().__init__(message)
