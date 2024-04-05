from pydantic import BaseModel, Field
from enum import Enum
from bson.objectid import ObjectId
from typing import Optional
import datetime


class VideoStatus(str, Enum):
    REQUESTED = "requested"
    SCRIPT_GENERATION_STARTED = "script_generation_started"
    SCRIPT_GENERATION_COMPLETE = "script_generation_complete"
    # PROCESSING = "processing"
    # COMPLETED = "completed"


class Video(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    request_id: str
    lang: str
    topic: str
    style: str
    status: VideoStatus = VideoStatus.REQUESTED
    aspect_ratio: str
    length: int
    title: Optional[str] = None
    script: Optional[str] = None
    script_generated: Optional[bool] = False
    title_generated: Optional[bool] = False
    script_generation_processing_start_time: Optional[datetime.datetime] = None
    script_generation_processing_end_time: Optional[datetime.datetime] = None
    script_generation_processing_duration: Optional[float] = None
