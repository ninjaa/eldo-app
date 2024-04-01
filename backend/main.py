from typing import List, Literal
import os
from typing import Union
import logging

from fastapi import FastAPI, File, UploadFile, Path, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from bson.objectid import ObjectId
from fastapi.middleware.cors import CORSMiddleware
import magic
from enum import Enum

from lib.database import get_db_connection

client, db, videos, assets = get_db_connection()
video_requests = db.get_collection("video_requests")

load_dotenv()


app = FastAPI()
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn")

UPLOAD_DIRECTORY = "media"

client, db, videos, assets = get_db_connection()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/video-request/")
def create_video_request(video_request: VideoRequest):
    request_id = str(ObjectId())
    video_request_dict = video_request.model_dump()
    video_request_dict["_id"] = request_id
    video_requests.insert_one(video_request_dict)
    return {"request_id": request_id}


class AssetStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageMetadata(BaseModel):
    width: int = -1
    height: int = -1
    content_type: Literal["image"]


class VideoMetadata(BaseModel):
    duration: float = -1
    width: int = -1
    height: int = -1
    fps: float = -1
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

    @validator("metadata", pre=True, always=True)
    def set_metadata_content_type(cls, value, values):
        if value is None:
            content_type = values["content_type"].split("/")[0]
            if content_type == "image":
                return ImageMetadata(content_type="image")
            elif content_type == "video":
                return VideoMetadata(content_type="video")
        return value


@app.post("/video-request/{request_id}/media")
async def upload_media(request_id: str = Path(...), file: UploadFile = File(...)):
    # Check if an asset with the same filename already exists for the video request
    existing_asset = assets.find_one(
        {"request_id": request_id, "filename": file.filename})
    if existing_asset:
        return Response(status_code=204)

    # Generate a new asset ID
    asset_id = str(ObjectId())

    # Create the directory for the video request if it doesn't exist
    request_directory = os.path.join(UPLOAD_DIRECTORY, request_id, "uploads")
    os.makedirs(request_directory, exist_ok=True)

    # Save the file to disk using its actual filename
    file_path = os.path.join(request_directory, file.filename)
    with open(file_path, "wb") as file_object:
        file_object.write(await file.read())

    # Detect the content type using python-magic
    content_type = magic.from_file(file_path, mime=True)
    file_extension = os.path.splitext(file.filename)[1]
    filename_without_extension = os.path.splitext(file.filename)[0]

    # Create the asset document using Pydantic models
    asset = Asset(
        _id=asset_id,
        request_id=request_id,
        filename=file.filename,
        content_type=content_type,
        file_path=file_path,
        file_extension=file_extension,
        filename_without_extension=filename_without_extension
    )

    # Save the asset in MongoDB
    assets.insert_one(asset.model_dump(by_alias=True))

    return {"asset_id": asset_id}


@app.post("/video-request/{request_id}/finalize")
async def finalize_video_request(request_id: str = Path(...)):
    # Find the video request by its ID
    video_request = video_requests.find_one({"_id": request_id})

    if video_request:
        # Check if the video request status is "pending"
        if video_request["status"] == "pending":
            # Update the video request status to "processing"
            video_requests.update_one(
                {"_id": ObjectId(request_id)},
                {"$set": {"status": "processing"}}
            )

            # # Create video objects for each requested format
            # for format in video_request["formats"]:
            #     video = {
            #         "request_id": request_id,
            #         "lang": video_request["lang"],
            #         "topic": video_request["topic"],
            #         "style": video_request["style"],
            #         "status": "pending",
            #         "aspect_ratio": format["aspect_ratio"],
            #         "length": format["length"]
            #     }
            #     videos.insert_one(video)

            return {"message": "Video request finalized successfully"}
        else:
            return {"message": "Video request is not in the pending state"}
    else:
        return {"message": "Video request not found"}


# Health check

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/ping")
def ping():
    return client.admin.command('ping')
