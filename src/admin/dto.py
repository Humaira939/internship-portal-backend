from pydantic import BaseModel


class AdminSchema(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True