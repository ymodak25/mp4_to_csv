import os
import uuid
import shutil
from io import BytesIO
from zipfile import ZipFile

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, PlainTextResponse

from process_video import process_video

app = FastAPI()

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    # Enforce 100 MB limit on incoming requests
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            size = int(content_length)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="Upload too large. Max size is 100 MB.",
                )
        except ValueError:
            pass
    return await call_next(request)


@app.get("/")
async def root():
    return {"status": "ok", "message": "mp4_to_csv backend running"}


@app.get("/healthz")
async def healthz():
    return PlainTextResponse("ok")


@app.post("/upload")
async def upload_videos(
    before: UploadFile = File(...),
    after: UploadFile = File(...),
):
    # Ensure both are videos
    if not before.content_type.startswith("video/") or not after.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Both files must be video files.")

    # Create temp file paths
    temp_id = str(uuid.uuid4())
    before_input_path = f"before_{temp_id}.mp4"
    after_input_path = f"after_{temp_id}.mp4"
    before_output_path = f"before_{temp_id}.csv"
    after_output_path = f"after_{temp_id}.csv"

    try:
        # Save uploaded files to disk
        with open(before_input_path, "wb") as f:
            shutil.copyfileobj(before.file, f)

        with open(after_input_path, "wb") as f:
            shutil.copyfileobj(after.file, f)

        # Process each video -> CSV
        process_video(before_input_path, before_output_path)
        process_video(after_input_path, after_output_path)

        # Create ZIP in memory
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_file:
            zip_file.write(before_output_path, arcname="before.csv")
            zip_file.write(after_output_path, arcname="after.csv")
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="csv_results.zip"'
            },
        )

    finally:
        # Clean up temp files
        for path in [
            before_input_path,
            after_input_path,
            before_output_path,
            after_output_path,
        ]:
            if os.path.exists(path):
                os.remove(path)
