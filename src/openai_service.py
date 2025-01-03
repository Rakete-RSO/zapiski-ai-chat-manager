import openai

from .config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


# https://stackoverflow.com/questions/77284901/upload-an-image-to-chat-gpt-using-the-api
def get_completion(messages):
    """
    messages: A list of messages comprising the conversation so far. Depending on the
      [model](https://platform.openai.com/docs/models) you use, different message types (modalities) are supported, like
      [text](https://platform.openai.com/docs/guides/text-generation),
      [images](https://platform.openai.com/docs/guides/vision), and more

    This function returns the assistant's completion message.
    """
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=400,
    )
    # The response format for ChatCompletion
    assistant_message = completion.choices[0].message
    return assistant_message.content
