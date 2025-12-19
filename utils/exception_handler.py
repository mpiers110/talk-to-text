from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi import status
import logging

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler.
    Converts unhandled exceptions into safe 500 responses.
    """
    logger.exception(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"{exc}"
        }
    )
