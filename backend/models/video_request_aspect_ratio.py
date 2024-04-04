from pydantic import BaseModel, Field
from enum import Enum
from bson.objectid import ObjectId
import datetime
from typing import Optional


class VideoRequestAspectRatioStatus(str, Enum):
    PENDING = "pending"
    REQUESTED = "requested"
    CONVERSION_STARTED = "conversion_started"
    CONVERSION_COMPLETE = "conversion_complete"


class VideoRequestAspectRatio(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    request_id: str
    aspect_ratio: str
    status: VideoRequestAspectRatioStatus = VideoRequestAspectRatioStatus.PENDING
    conversion_attempts: int = 0
    conversion_start_time: Optional[datetime.datetime] = None
    conversion_end_time: Optional[datetime.datetime] = None
    conversion_duration: Optional[float] = None
