from typing import List, Literal
from pydantic import BaseModel, Field, validator
from typing import Union
from enum import Enum


class VideoFormat(BaseModel):
    aspect_ratio: str
    length: int


class VideoRequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    REQUESTED = "requested"  # After assets are described and converted


class VideoRequest(BaseModel):
    lang: str
    topic: str
    style: str
    status: VideoRequestStatus = VideoRequestStatus.PENDING
    formats: List[VideoFormat]


class VideoStatus(str, Enum):
    REQUESTED = "requested"
    # PROCESSING = "processing"
    # COMPLETED = "completed"


class Video(BaseModel):
    request_id: str
    lang: str
    topic: str
    style: str
    status: VideoStatus = VideoStatus.REQUESTED
    aspect_ratio: str
    length: int


class AssetStatus(str, Enum):
    UPLOADED = "uploaded"
    DESCRIPTION_STARTED = "description_started"
    DESCRIPTION_COMPLETE = "description_complete"
    DESCRIPTION_FAILED = "description_failed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageMetadata(BaseModel):
    width: int = -1
    height: int = -1
    aspect_ratio: str = ""
    content_type: Literal["image"]


class VideoMetadata(BaseModel):
    duration: float = -1
    width: int = -1
    height: int = -1
    fps: float = -1
    aspect_ratio: str = ""
    has_speech: bool = False
    content_type: Literal["video"]


class Asset(BaseModel):
    id: str = Field(alias="_id")
    request_id: str
    filename: str
    content_type: str
    file_path: str
    file_extension: str
    filename_without_extension: str
    description: str = ""
    transcript: str = ""
    processed: bool = False
    status: AssetStatus = AssetStatus.UPLOADED
    metadata: Union[ImageMetadata, VideoMetadata] = None
    description_attempts: int = 0

    @validator("metadata", pre=True, always=True)
    def set_metadata_content_type(cls, value, values):
        if value is None:
            content_type = values["content_type"].split("/")[0]
            if content_type == "image":
                return ImageMetadata(content_type="image")
            elif content_type == "video":
                return VideoMetadata(content_type="video")
        return value
