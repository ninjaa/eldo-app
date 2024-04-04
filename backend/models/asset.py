from pydantic import BaseModel, Field, validator
from typing import Union, Optional
from bson.objectid import ObjectId
from enum import Enum
import datetime

from models.upload import ImageMetadata, VideoMetadata


class AssetStatus(str, Enum):
    CONVERTED = "converted"
    DECOMMISSIONED = "decommissioned"


class Asset(BaseModel):
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
    status: AssetStatus = AssetStatus.CONVERTED
    metadata: Union[ImageMetadata, VideoMetadata] = None
    conversion_attempts: int = 0
    conversion_start_time: Optional[datetime.datetime] = None
    conversion_end_time: Optional[datetime.datetime] = None
    conversion_duration: Optional[float] = None

    @validator("metadata", pre=True, always=True)
    def set_metadata_content_type(cls, value, values):
        if value is None:
            content_type = values["content_type"].split("/")[0]
            if content_type == "image":
                return ImageMetadata(content_type="image")
            elif content_type == "video":
                return VideoMetadata(content_type="video")
        return value

# Remember to adjust the validator or any other logic specific to assets if needed.
