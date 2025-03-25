from pydantic import BaseModel


class UserCredentialsDTO(BaseModel):
    email: str
    password: str
