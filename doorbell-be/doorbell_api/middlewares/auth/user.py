from starlette.authentication import BaseUser

class User(BaseUser):
    def __init__(self) -> None:
        self._is_authenticated = False
        self._identity = "guest"

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, value: bool):
        self._is_authenticated = value

    @property
    def identity(self) -> str:
        return self._identity

    @identity.setter
    def identity(self, value: str):
        self._identity = value

    # Not in use, just to comply with starlette's BaseUser
    @property
    def display_name(self) -> str:
        return self._identity
