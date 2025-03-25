from pydantic import BaseModel


class HitsDTO(BaseModel):
    hits: int
