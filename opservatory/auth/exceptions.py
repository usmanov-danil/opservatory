class UserDoesNotExist(Exception):
    def __init__(self):
        super().__init__("User does not exist.")


class IncorrectPassword(Exception):
    def __init__(self):
        super().__init__("Incorrect password.")


class UserAlreadyExists(Exception):
    def __init__(self):
        super().__init__("User already exists.")


class UnableToValidateToken(Exception):
    def __init__(self):
        super().__init__("Unable to validate token.")
