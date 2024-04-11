import datetime
from bson.objectid import ObjectId
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class SceneStatus(str, Enum):
    GENERATED = "generated"
    NARRATION_QUEUED = "narration_queued"
    NARRATION_STARTED = "narration_started"
    NARRATION_COMPLETE = "narration_complete"
    NARRATION_FAILED = "narration_failed"


class Scene(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    video_id: str
    request_id: str
    scene_type: Optional[str] = None
    aspect_ratio: str
    status: SceneStatus
    narration: Optional[str] = None
    narration_audio_filename: Optional[str] = None
    narration_language: Optional[str] = None
    duration: Optional[float] = None
    asset_filename: Optional[str] = None
    prev_scene_id: Optional[str] = None
    next_scene_id: Optional[str] = None
    scene_narration_attempts: int = 0
    scene_narration_start_time: Optional[datetime.datetime] = None
    scene_narration_end_time: Optional[datetime.datetime] = None
    scene_narration_duration: Optional[float] = None
