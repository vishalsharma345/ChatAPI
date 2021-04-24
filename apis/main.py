from fastapi import FastAPI, Depends, HTTPException, status
from model import *
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
import pymongo
from typing import Optional
import jwt
import secrets
import os
import time
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
from fastapi.responses import FileResponse
import json
import uvicorn


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
client = pymongo.MongoClient("localhost", 27017)
db = client.chatdb
# client = pymongo.MongoClient("mongodb://chatuser:chat123@mongodb:27017/chatdb")
# db = client["chatdb"]
JWT_SECRET = 'myjwtsecret'


# Authenticate User
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        username = payload.get("username")
        password = payload.get("password")
        user = db.users.find_one({"username": username, "password": password})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        data = {
            "id": str(user["_id"]),
            "username": user["username"],
            "full_name": user["name"],
            "email": user["email"],
            "password": user["password"]
        }
        return data
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Username and Password")


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


# User Login to Generate Token
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = db.users.find_one({"username": form_data.username, "password": form_data.password})
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    data = {
        "username": user_dict["username"],
        "full_name": user_dict["name"],
        "email": user_dict["email"],
        "password": user_dict["password"]
    }
    token = jwt.encode(data, JWT_SECRET)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


#  Sign Up or Register User
@app.post("/signup")
async def register_user(model: User):

    exists = db.users.find_one({'email': model.email})
    if exists:
        return {"status": "false", "msg": "Email id already exists."}
    else:
        username = model.email.split("@")[0]
        obj_id = db.users.insert_one({"username": username, "email": model.email, "name": model.full_name,
                                      "password": model.password}).inserted_id

    return {"status": "true", "msg": "Success",
            "data": {"id": str(obj_id), 'name': model.full_name, 'email': model.email}}


# Creating Group
@app.post("/create_group")
def create_group(model: CreateGroup, auth: User = Depends(get_current_active_user)):
    timestamp = str(int(time.time()))
    group_id = db.groups.insert_one({'created_by': auth["username"], 'group_name': model.group_name,
                                     'timestamp': timestamp, 'participants': [{"username": auth["username"],
                                                                               "add_timestamp":timestamp}],
                                     'msg': []}).inserted_id
    return {"status": "true", "msg": "Success", 'data': {"group_id": str(group_id)}}


# Add Participants in the Group
@app.post("/add_participants")
def add_participants(model: AddParticipants, auth: User = Depends(get_current_active_user)):
    timestamp = str(int(time.time()))
    db.groups.update_one({"_id": ObjectId(model.group_id)}, {"$push": {"participants": {"username": model.username,
                                                                                         "add_timestamp": timestamp}}})
    return {"status": "true", "msg": "Success"}


#  Get Participants By the Group
@app.post("/get_all_participants")
def get_all_participants(model: GetAllParticipants, auth: User = Depends(get_current_active_user)):
    data = db.groups.find({"_id": ObjectId(model.group_id)})
    list_data = []
    for i in data:
        for j in i['participants']:
            list_data.append(j)
    return {"status": "true", "msg": "Success", "data": list_data}


# Sending Message
@app.post("/send_msg")
def send_msg(model: Messages, auth: User = Depends(get_current_active_user)):
    timestamp = str(int(time.time()))
    msg = db.message.insert_one({"sender": model.sender, 'msg': model.msg, "add_timestamp": timestamp,
                                 "like_by": [], "like_count":0}).inserted_id
    db.groups.update_one({"_id": ObjectId(model.group_id)}, {"$push": {"msg": {"msg_id": str(msg)}}})
    return {"status": "true", "msg": "Success"}


# Get All Message By the Group
@app.post("/get_msg")
def get_msg(model: GetMessage, auth: User = Depends(get_current_active_user)):
    data = db.groups.find({"_id": ObjectId(model.group_id)})
    list_data = []
    for i in data:
        for j in i['msg']:
            msg = db.message.find({"_id": ObjectId(j["msg_id"])})
            for k in msg:
                msgdict = {
                    "msg_id": str(k["_id"]),
                    "sender": k["sender"],
                    "msg": k["msg"],
                    "timestamp": k["add_timestamp"],
                    "like_count": k["like_count"]
                }
                list_data.append(msgdict)
    return {"status": "true", "msg": "Success", "data": list_data}


# Message Likes
@app.post("/like_msg")
def like_msg(model:LikeMessage, auth: User = Depends(get_current_active_user)):
    db.message.update_one({"_id": ObjectId(model.message_id)}, {"$push": {"like_by": {"username": model.username}},
                              '$inc': {'like_count': 1}}, upsert=True)
    return {"status": "true", "msg": "Success"}


# Get Like Details
@app.post("/like_details")
def like_details(model: LikeDetails, auth: User = Depends(get_current_active_user)):
    msg = db.message.find({"_id": ObjectId(model.message_id)}, {"like_by": 1,"_id":0})
    list_data = []
    for k in msg:
        list_data.append(k)
    return {"status": "true", "msg": "Success", "data":list_data}


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", port=8080)

