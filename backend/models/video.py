from pydantic import BaseModel, Field
from enum import Enum
from bson.objectid import ObjectId


class VideoStatus(str, Enum):
    SPAWNED = "spawned"
    # PROCESSING = "processing"
    # COMPLETED = "completed"


class Video(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    request_id: str
    lang: str
    topic: str
    style: str
    status: VideoStatus = VideoStatus.SPAWNED
    aspect_ratio: str
    length: int

