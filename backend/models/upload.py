import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, validator
from typing import Union
from enum import Enum
from bson.objectid import ObjectId


class UploadStatus(str, Enum):
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
    is_logo: bool = False
    is_profile_pic: bool = False


class VideoMetadata(BaseModel):
    duration: float = -1
    width: int = -1
    height: int = -1
    fps: float = -1
    aspect_ratio: str = ""
    has_speech: bool = False
    content_type: Literal["video"]


class Upload(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    request_id: str
    filename: str
    content_type: str
    file_path: str
    file_extension: str
    filename_without_extension: str
    description: str = ""
    transcript: str = ""
    processed: bool = False
    status: UploadStatus = UploadStatus.UPLOADED
    metadata: Union[ImageMetadata, VideoMetadata] = None
    description_attempts: int = 0
    description_start_time: Optional[datetime.datetime] = None
    description_end_time: Optional[datetime.datetime] = None

    @validator("metadata", pre=True, always=True)
    def set_metadata_content_type(cls, value, values):
        if value is None:
            content_type = values["content_type"].split("/")[0]
            if content_type == "image":
                return ImageMetadata(content_type="image")
            elif content_type == "video":
                return VideoMetadata(content_type="video")
        return value
