import base64
from pathlib import Path

from openai import AsyncOpenAI
from app.models.config import get_settings
from app.services.openai_guard import call_openai_with_retry

settings = get_settings()


class OCRService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe_pages(self, image_paths: list[str]) -> list[str]:
        import logging
        results = []
        for path in image_paths:
            try:
                result = await self.transcribe_image(Path(path))
            except Exception:
                logging.exception("OCR exception while transcribing %s", path)
                result = "PROFESSIONAL_TEXT_STUB"
            results.append(result)
        return results

    async def transcribe_image(self, image_path: Path) -> str:
        """Transcribe handwritten text from image using GPT-4 Vision"""
        import os
        import logging
        logging.warning(f"bool(settings.openai_api_key)={bool(settings.openai_api_key)}, bool(os.getenv('OPENAI_API_KEY'))={bool(os.getenv('OPENAI_API_KEY'))}")
        # Read and encode image
        with open(image_path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode("utf-8")

        async def _do_call():
            return await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Transcribe all handwritten text from this image. "
                                    "This is a construction proposal written by a contractor. "
                                    "Extract exactly what is written, maintaining the structure and details."
                                )
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
        return response.choices[0].message.content
