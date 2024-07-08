#!/usr/bin/env python3

from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api import create_app
from store import ProjectStore
import traceback

project_store = ProjectStore(Path("./prod"))
app = create_app(project_store)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": traceback.format_exc()},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": str(exc), "traceback": traceback.format_exc()},
    )


if __name__ == "__main__":
    uvicorn.run("serve:app", host="0.0.0.0", port=4000, reload=True, log_level="error")
