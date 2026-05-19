class EmailAlreadyRegistered(Exception):
    pass

class EmailNotFound(Exception):
    pass

class PasswordNotValid(Exception):
    pass

class EmailNotConfirmed(Exception):
    pass

class InvalidSessionError(Exception):
    pass

class UserNotFound(Exception):
    pass
