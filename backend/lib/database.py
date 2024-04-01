import os
import pymongo
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    MONGO_URL = os.getenv("MONGO_URL")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

    client = pymongo.MongoClient(MONGO_URL, tls=True)
    client.start_session()
    db = client.get_database(MONGO_DB_NAME)
    videos = db.get_collection("videos")
    assets = db.get_collection("assets")

    return client, db, videos, assets
