from typing import List

from pydantic import BaseModel, Field


class TranscribeRequest(BaseModel):
    file_url: str
    request_prompt: str = ""
    language: str = "auto"
    phrases: List[str] = Field(default_factory=list)
    diarization: bool = False
    duration_seconds: float = 0.0


class TranscribeResponse(BaseModel):
    status: str = "success"
    segments: List[dict] = Field(default_factory=list)
    delay: float = 0.0
    spend: float = 0.0
    nodename: str = ""
