from contextlib import asynccontextmanager
from datetime import datetime
from operator import and_
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .auth import verify_access_token
from .database import create_tables, get_db
from .models import Chat, Message
from .schemas import ChatUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup code
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.get("/chat")
def list_chats(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if not payload:
        return {"msg": "Invalid token"}
    user_id = payload["sub"]
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
        .all()
    )
    return [
        {
            "id": chat.id,
            "name": chat.name,
            "created_at": chat.created_at,
        }
        for chat in chats
    ]


@app.patch("/chat/{id}", response_model=dict)
def update_chat(
    id: UUID,
    chat_update: ChatUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    # Verify the access token
    payload = verify_access_token(token)
    if not payload:
        return {"msg": "Invalid token"}
    user_id = payload["sub"]
    # Check if the user is the owner of the chat
    chat = db.query(Chat).filter(Chat.id == id, Chat.user_id == user_id).first()
    if not chat:
        return {"msg": "Chat not found"}
    # Update the chat
    chat.name = chat_update.name
    db.commit()
    return {
        "id": chat.id,
        "name": chat.name,
        "created_at": chat.created_at,
    }
