from contextlib import asynccontextmanager
from datetime import datetime
from operator import or_
from uuid import UUID

from fastapi import Depends, FastAPI
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
        if chat.name != ""
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


@app.get("/chat/{id}", response_model=dict)
def get_chat_messages(
    id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = verify_access_token(token)
    if not payload:
        return {"msg": "Invalid token"}
    user_id = payload["sub"]
    chat = db.query(Chat).filter(Chat.id == id, Chat.user_id == user_id).first()
    if not chat:
        return {"msg": "Chat not found"}

    previous_messages = (
        db.query(Message)
        .filter(
            Message.chat_id == id,
            or_(Message.role == "user", Message.role == "assistant"),
        )
        .all()
    )

    return {
        "id": chat.id,
        "name": chat.name,
        "messages": [
            {"role": msg.role, "content": msg.content} for msg in previous_messages
        ],
    }


@app.post("/chat")
def create_chat(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if not payload:
        return {"msg": "Invalid token"}
    user_id = payload["sub"]
    new_chat = Chat(user_id=user_id, created_at=datetime.now(), name="")
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    # Insert the system prompt message
    system_prompt = (
        "Si asistent za izdelovanje študijskih zapiskov. Iz danega gradiva (teksta ali slik) pomagaj zapisati zapise, "
        + "ki bodo temu človeku pomagale pri študiju. Če v zapiskih kje omeni tehnični pojem (na primer Jakobinska matrika) "
        + "pojasni teorijo za tem pojmom"
        + "VEDNO: Odgovarjaj v slovenščini, tudi če gre za vprašanje v angleščini ali drugih jezikih"
    )
    system_message = Message(
        chat_id=new_chat.id,
        content=system_prompt,
        role="system",
        visible=False,
        created_at=datetime.now(),
    )
    db.add(system_message)
    db.commit()
    db.refresh(system_message)

    return {"chat_id": new_chat.id}
