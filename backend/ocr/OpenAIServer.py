#import json

from openai import OpenAI


class OpenAIClient:
    __key_path__ = ".venv/CHATGPT_API"

    def __init__(self, key):
        self.client = OpenAI(api_key=key)
        self.messages = list()

    @classmethod
    def new_client(cls) -> "OpenAIClient":
        with open(cls.__key_path__, "r") as file:
            key = file.readline()
        return cls(key)

    def prompt(
        self,
        user_prompt: str,
        image_file :str,
        system_prompt: str | None = None,
    ) -> dict:

        if system_prompt is not None:
            self.messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )
        self.messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini", messages=self.messages,
        )
        output = completion.choices[0].message
        self.messages.append(output)
        content = output.content
        returned_tools = []
        return {"content": content, "tools": returned_tools}


client = OpenAIClient.new_client()

