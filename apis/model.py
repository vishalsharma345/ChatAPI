from pydantic import BaseModel


class User(BaseModel):
    email: str
    full_name: str
    password: str


class Messages(BaseModel):
    msg: str
    sender: str
    group_id: str


class AddParticipants(BaseModel):
    username: str
    group_id: str


class GetAllParticipants(BaseModel):
    group_id: str


class CreateGroup(BaseModel):
    group_name: str


class GetMessage(BaseModel):
    group_id: str


class LikeMessage(BaseModel):
    username: str
    like: str
    message_id: str


class LikeDetails(BaseModel):
    message_id: str