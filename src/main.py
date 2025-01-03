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
from .openai_service import get_completion
from .util import build_openai_input, format_base64_image, get_image_base64


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup code
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.post("/chat")
def create_chat(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if not payload:
        return {"msg": "Invalid token"}
    user_id = payload["sub"]
    new_chat = Chat(user_id=user_id, created_at=datetime.now())
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


@app.post("/chat/messages")
def create_message(
    chat_id: UUID = Form(...),
    message: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    # Verify the token
    payload = verify_access_token(token)
    if not payload:
        return {"msg": "Invalid token"}
    user_id = payload["sub"]
    if not user_id:
        return {"msg": "Invalid token payload"}

    # Get the chat from the database
    chat = (
        db.query(Chat).filter(and_(Chat.id == chat_id, Chat.user_id == user_id)).first()
    )
    if not chat:
        return {"msg": "Chat not found"}

    formatted_base64_image = ""
    if file:
        filetype = (file.filename or "").split(".")[-1]
        base64_image = get_image_base64(file)
        if base64_image:
            formatted_base64_image = format_base64_image(base64_image, filetype)
    # Get the system message from the database
    previous_messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    if not previous_messages:
        return {"msg": "No messages found, expected at least system message"}
    openai_messages = build_openai_input(
        previous_messages, message, formatted_base64_image
    )
    assistant_message = get_completion(openai_messages)
    user_message_db = Message(
        chat_id=chat_id,
        content=message,
        role="user",
        visible=True,
        created_at=datetime.now(),
        base64_image=formatted_base64_image,
    )
    assistant_message_db = Message(
        chat_id=chat_id,
        content=assistant_message,
        role="assistant",
        visible=True,
        created_at=datetime.now(),
    )
    db.add(user_message_db)
    db.add(assistant_message_db)
    db.commit()
    db.refresh(user_message_db)
    db.refresh(assistant_message_db)

    return {"message_id": user_message_db.id, "content": assistant_message_db.content}
