from openai import AsyncOpenAI
from app.models.config import get_settings
from typing import List
import base64

settings = get_settings()


class BookOCRService:
    """OCR service for book transcription - exact word-for-word transcription"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def transcribe_pages(self, image_paths: List[str]) -> str:
        """Transcribe multiple book pages in order, preserving exact text"""
        
        all_text = []
        
        for i, image_path in enumerate(image_paths, 1):
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise transcription assistant. "
                            "Transcribe the handwritten text EXACTLY as written, word-for-word. "
                            "DO NOT:\n"
                            "- Change, rephrase, or improve any wording\n"
                            "- Fix grammar or spelling unless clearly an error\n"
                            "- Add punctuation that isn't there\n"
                            "- Skip or summarize anything\n\n"
                            "DO:\n"
                            "- Preserve the exact words and phrasing\n"
                            "- Maintain paragraph breaks\n"
                            "- Use [illegible] if you cannot read a word\n"
                            "- Transcribe everything visible on the page"
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Transcribe this handwritten page (Page {i}):"
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
            
            page_text = response.choices[0].message.content
            all_text.append(f"[Page {i}]\n\n{page_text}")
        
        return "\n\n".join(all_text)
