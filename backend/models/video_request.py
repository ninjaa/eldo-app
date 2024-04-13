from pydantic import BaseModel, Field
from enum import Enum
from bson.objectid import ObjectId
from typing import Optional


class VideoRequestStatus(str, Enum):
    PENDING = "pending"
    REQUESTED = "requested"  # After the request is received
    # After assets are described and converted
    SPAWNING_STARTED = "spawning_started"
    SPAWNING_COMPLETED = "spawning_completed"


class VideoRequest(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    lang: str
    topic: str
    style: str
    status: VideoRequestStatus = VideoRequestStatus.PENDING
    spawning_attempts: int = 0
    brand_link: Optional[str] = None
