
import re
from lib.database import get_db_connection
from models.upload import Upload
_client, db = get_db_connection()


def get_logo_upload(request_id):
    upload_result = db.uploads.find_one(
        {"request_id": request_id, "metadata.is_logo": True})
    if upload_result is None:
        return None
    return Upload(**upload_result)


def get_brand_link(request_id):
    # @TODO add this to the request json and in the db
    return "https://twitter.com/MultiOn_AI"


def slugify(value):
    """
    Convert spaces to hyphens. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase.
    """

    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)
