from typing import List, Optional
from pydantic import BaseModel

class WarningMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None


class AppResponse(BaseModel):
    status: str
    data: Optional[dict] = None
    error: Optional[dict] = None
    warnings: Optional[List[WarningMessage]] = None
