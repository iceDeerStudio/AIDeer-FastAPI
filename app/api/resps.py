from app.models.server import ExceptionDetail
from typing import ClassVar, Dict, Any

# Path: app/api/resps.py


class ExceptionResponse(ExceptionDetail):

    RESPONSES: ClassVar[Dict[int, Dict[str, Any]]] = {
        400: {"model": ExceptionDetail, "description": "Bad request"},
        401: {"model": ExceptionDetail, "description": "Unauthorized"},
        402: {
            "model": ExceptionDetail,
            "description": "Insufficient credits",
        },
        403: {"model": ExceptionDetail, "description": "Insufficient permissions"},
        404: {"model": ExceptionDetail, "description": "Not found"},
        422: {"model": ExceptionDetail, "description": "Unprocessable entity"},
        500: {"model": ExceptionDetail, "description": "Internal server error"},
        501: {"model": ExceptionDetail, "description": "Not implemented"},
    }

    @staticmethod
    def get_responses(*status_codes: int) -> Dict[int, Dict[str, Any]]:
        response = {}
        for code in status_codes:
            response[code] = ExceptionResponse.RESPONSES[code]
        return response
