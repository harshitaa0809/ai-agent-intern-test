import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class LLMClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4.1")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:

        response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=user_message,
        )

        return response.output_text