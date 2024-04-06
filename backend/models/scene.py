import datetime
from bson.objectid import ObjectId
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class SceneStatus(str, Enum):
    GENERATED = "generated"
    NARRATED = "narrated"
    SCRIPTED = "scripted"


class Scene(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    video_id: str
    request_id: str
    scene_type: Optional[str] = None
    aspect_ratio: str
    status: SceneStatus
    narration: Optional[str] = None
    asset_filename: Optional[str] = None
    prev_scene_id: Optional[str] = None
    next_scene_id: Optional[str] = None
    narration_attempts: int = 0
    narration_start_time: Optional[datetime.datetime] = None
    narration_end_time: Optional[datetime.datetime] = None
    narration_duration: Optional[float] = None
