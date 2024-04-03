import datetime
from typing import List
from pydantic import BaseModel

from models.video_request import VideoRequestStatus


class InputVideoFormat(BaseModel):
    aspect_ratio: str
    length: int


class InputVideoRequest(BaseModel):
    lang: str
    topic: str
    style: str
    status: VideoRequestStatus = VideoRequestStatus.PENDING
    formats: List[InputVideoFormat]
    spawning_attempts: int = 0
