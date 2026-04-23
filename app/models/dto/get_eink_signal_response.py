from http import HTTPStatus

from pydantic import BaseModel


class GetEinkSignalResponse(BaseModel):
    status: HTTPStatus
    message: str
