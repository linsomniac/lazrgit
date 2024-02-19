#!/usr/bin/env python

from openai import OpenAI
from . import internal


class OpenAIContext:
    def __init__(self):
        self.client = None

    def setup(self) -> None:
        if self.client is not None:
            return

        self.client = OpenAI(
            api_key = internal.context.config.get("openai", "key")
        )

        if internal.context.config.has_option("openai", "model"):
            self.model = internal.context.config.get("openai", "model")
        else:
            self.model = 'gpt-3.5-turbo'


openaictx = OpenAIContext()


def ask_openai(system_prompt: str, user_prompt: str):
    openaictx.setup()

    response = openaictx.client.chat.completions.create(
        messages=[{ "role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}],
        model=openaictx.model,
    )

    return response.choices[0].message.content
