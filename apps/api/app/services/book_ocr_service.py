
from openai import AsyncOpenAI
from app.models.config import get_settings
from typing import List
import base64
from app.services.openai_guard import call_openai_with_retry

settings = get_settings()


class BookOCRService:
    """OCR service for book transcription - exact word-for-word transcription"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def transcribe_pages(self, image_paths: List[str]) -> str:
        """Transcribe multiple book pages in order, preserving exact text"""
        parts: list[str] = []
        for i, image_path in enumerate(image_paths, 1):
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            async def _do_call():
                return await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Transcribe all visible text from the image(s) verbatim. Preserve line breaks. If a word is unclear, write [illegible]. Do not add commentary."
                            )
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Transcribe this page (Page {i}):"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000
                )

            response = await call_openai_with_retry(_do_call, max_attempts=3, per_attempt_timeout_s=20.0)
            page_text = response.choices[0].message.content
            parts.append(f"--- Page {i} ---\n{page_text}")
        return "\n\n---\n\n".join(parts)
