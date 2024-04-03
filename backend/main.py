
from lib.models import Upload, VideoRequest
import os

from fastapi import FastAPI, File, UploadFile, Path, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware


from dotenv import load_dotenv
from bson.objectid import ObjectId
from fastapi.middleware.cors import CORSMiddleware
import magic

from lib.database import get_db_connection
from lib.logger import setup_logger

client, db, video_requests_collection, videos_collection, uploads_collection, assets_collection = get_db_connection()

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

logger = setup_logger("uvicorn")

UPLOAD_DIRECTORY = "media"

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


@app.post("/video-request/")
def create_video_request(video_request: VideoRequest):
    request_id = str(ObjectId())
    video_request_dict = video_request.model_dump()
    video_request_dict["_id"] = request_id
    video_requests_collection.insert_one(video_request_dict)
    return {"request_id": request_id}


@app.post("/video-request/{request_id}/media")
async def upload_media(request_id: str = Path(...), file: UploadFile = File(...)):
    # Check if an upload with the same filename already exists for the video request
    existing_upload = uploads_collection.find_one(
        {"request_id": request_id, "filename": file.filename})
    if existing_upload:
        return Response(status_code=204)

    # Generate a new asset ID
    upload_id = str(ObjectId())

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
    upload = Upload(
        _id=upload_id,
        request_id=request_id,
        filename=file.filename,
        content_type=content_type,
        file_path=file_path,
        file_extension=file_extension,
        filename_without_extension=filename_without_extension
    )

    # Save the asset in MongoDB
    uploads_collection.insert_one(upload.model_dump(by_alias=True))

    return {"upload_id": upload_id}


@app.post("/video-request/{request_id}/finalize")
async def finalize_video_request(request_id: str = Path(...)):
    # Find the video request by its ID
    video_request = video_requests_collection.find_one({"_id": request_id})

    if video_request:
        # Check if the video request status is "pending"
        if video_request["status"] == "pending":
            # Update the video request status to "requested"
            video_requests_collection.update_one(
                {"_id": request_id},
                {"$set": {"status": "requested"}}
            )

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
