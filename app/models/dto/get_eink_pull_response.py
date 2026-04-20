from pydantic import BaseModel
from typing import Optional


class GetEinkPullResponseData(BaseModel):
    next_cron_time: str
    image_url: Optional[str]


class GetEinkPullResponse(BaseModel):
    status: int
    type: Optional[str]
    message: str
    data: GetEinkPullResponseData
