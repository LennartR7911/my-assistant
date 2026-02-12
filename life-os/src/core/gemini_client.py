from typing import Optional, Any
from google import genai
from google.genai import types
from src.core.config import settings
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = "gemini-2.0-flash-exp"

    def generate_content(self, prompt: str, context: str = "") -> Optional[str]:
        try:
            full_prompt = f"Context: {context}\n\nTask: {prompt}" if context else prompt
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return None

    def upload_file(self, file_path: str, mime_type: Optional[str] = None) -> Any:
        try:
            # Note: The new SDK supports direct file path in upload()
            upload_result = self.client.files.upload(
                file=file_path,
                config=dict(mime_type=mime_type) if mime_type else None
            )
            logger.info(f"Uploaded file: {upload_result.name}")
            return upload_result
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return None

    def process_audio(self, audio_path: str, prompt: str) -> Optional[str]:
        """
        Uploads audio, waits for processing, and generates content.
        """
        try:
            uploaded_file = self.upload_file(audio_path, mime_type="audio/mp3")

            if not uploaded_file:
                return None

            # Poll for state active
            while uploaded_file.state == "PROCESSING":
                time.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)

            if uploaded_file.state != "ACTIVE":
                logger.error(f"File upload failed state: {uploaded_file.state}")
                return None

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(
                                file_uri=uploaded_file.uri,
                                mime_type=uploaded_file.mime_type),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ]
            )
            return response.text

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return None
