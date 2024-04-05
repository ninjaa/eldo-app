from pydantic import BaseModel, Field
from enum import Enum
from bson.objectid import ObjectId
from typing import Optional
import datetime

class VideoRequestFormatStatus(str, Enum):
    PENDING = "pending"
    REQUESTED = "requested"
    CONVERTED = "converted"
    SPAWNING_STARTED = "spawning_started"
    SPAWNING_COMPLETE = "spawning_started"
    GENERATED = "generated"


class VideoRequestFormat(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    request_id: str
    aspect_ratio: str
    length: int
    status: VideoRequestFormatStatus = VideoRequestFormatStatus.PENDING
    spawning_attempts: int = 0
    spawning_start_time: Optional[datetime.datetime] = None
    spawning_end_time: Optional[datetime.datetime] = None
    spawning_duration: Optional[float] = None
