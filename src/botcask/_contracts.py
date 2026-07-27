from pydantic import BaseModel


class ResponseSpec(BaseModel):
    text: str


class CommandSpec(BaseModel):
    response: ResponseSpec
