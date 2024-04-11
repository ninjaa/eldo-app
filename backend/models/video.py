from pydantic import BaseModel, Field
from enum import Enum
from bson.objectid import ObjectId
from typing import Optional
import datetime


class VideoStatus(str, Enum):
    REQUESTED = "requested"
    SCRIPT_GENERATION_STARTED = "script_generation_started"
    SCRIPT_GENERATION_COMPLETE = "script_generation_complete"
    SCENE_EXTRACTION_QUEUED = "scene_extraction_queued"
    SCENE_EXTRACTION_STARTED = "scene_extraction_started"
    SCENE_EXTRACTION_COMPLETE = "scene_extraction_complete"
    SCENE_NARRATION_STARTED = "scene_narration_started"
    SCENE_NARRATION_COMPLETE = "scene_narration_complete"
    # PROCESSING = "processing"
    # COMPLETED = "completed"


class Video(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    request_id: str
    lang: str
    topic: str
    style: str
    status: VideoStatus = VideoStatus.REQUESTED
    aspect_ratio: str
    length: int
    
    # Script Generation
    title: Optional[str] = None
    script: Optional[str] = None
    script_generated: Optional[bool] = False
    title_generated: Optional[bool] = False
    script_generation_processing_start_time: Optional[datetime.datetime] = None
    script_generation_processing_end_time: Optional[datetime.datetime] = None
    script_generation_processing_duration: Optional[float] = None
    script_generation_attempts: int = 0
    
    # Scene Extraction
    scene_extraction_start_time: Optional[datetime.datetime] = None
    scene_extraction_end_time: Optional[datetime.datetime] = None
    scene_extraction_duration: Optional[float] = None
    scene_extraction_attempts: int = 0
    
    # Scene Narration
    scene_narration_start_time: Optional[datetime.datetime] = None
    scene_narration_end_time: Optional[datetime.datetime] = None
    scene_narration_duration: Optional[float] = None
    scene_narration_attempts: int = 0
    
