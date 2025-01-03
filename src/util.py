import base64

from fastapi import HTTPException, UploadFile, status

from .models import Message


def get_image_base64(file: UploadFile) -> str:
    base64_image = ""
    if file:
        try:
            # Read the file content
            file_content = file.file.read()
            # Encode to base64
            base64_image = base64.b64encode(file_content).decode("utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process file: {str(e)}",
            )
        finally:
            file.file.close()
    return base64_image


def format_base64_image(base64_image: str, filetype: str) -> str:
    return f"data:image/{filetype};base64,{base64_image}"


# messages: A list of messages comprising the conversation so far. Depending on the
#   [model](https://platform.openai.com/docs/models) you use, different message
#   types (modalities) are supported, like
#   [text](https://platform.openai.com/docs/guides/text-generation),
#   [images](https://platform.openai.com/docs/guides/vision), and
#   and more
def build_openai_input(
    previous_messages: list[Message], user_input: str, base64_image: str
):
    output = []
    for message in previous_messages:
        content = []
        if message.content:
            content.append({"type": "text", "text": message.content})
        if message.base64_image:
            content.append(
                {"type": "image_url", "image_url": {"url": message.base64_image}}
            )
        output.append({"role": message.role, "content": message.content})

    new_content = []
    if base64_image:
        new_content.append({"type": "image_url", "image_url": {"url": base64_image}})
    if user_input:
        new_content.append({"type": "text", "text": user_input})
    output.append({"role": "user", "content": new_content})
    return output
