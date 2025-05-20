import jwt
from datetime import datetime

from ..exceptions import DecodeTokenException, ExpiredTokenException


class TokenHelper:
    @staticmethod
    def encode(payload: dict, key: str, expire_period: datetime, config) -> str:
        token = jwt.encode(
            payload={
                **payload,
                "exp": expire_period,
            },
            key=key,
            algorithm=config['jwt']['algorithm'],
        )
        return token

    @staticmethod
    def decode(*, token: str, refresh: bool = True, config) -> dict:
        key = config["jwt"]["refresh"]["key"] if refresh else config["jwt"]["access"]["key"]
        try:
            return jwt.decode(
                token,
                key,
                config['jwt']['algorithm'],
            )
        except jwt.exceptions.DecodeError:
            raise DecodeTokenException
        except jwt.exceptions.ExpiredSignatureError:
            raise ExpiredTokenException
