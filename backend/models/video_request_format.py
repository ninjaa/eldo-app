from pydantic import BaseModel, Field
from enum import Enum
from bson.objectid import ObjectId


class VideoRequestFormatStatus(str, Enum):
    PENDING = "pending"
    REQUESTED = "requested"
    CONVERTED = "converted"
    SPAWNED = "success"
    GENERATED = "generated"


class VideoRequestFormat(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    request_id: str
    aspect_ratio: str
    length: int
    status: VideoRequestFormatStatus = VideoRequestFormatStatus.PENDING
