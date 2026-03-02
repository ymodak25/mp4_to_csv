import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import zipfile

from process_video import process_video


app = FastAPI()

# Allow your Google Sites / other frontends to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "mp4_to_csv backend running"}


@app.get("/healthz")
def healthz():
    return "ok"


@app.post("/upload")
async def upload_videos(
    before: UploadFile = File(...),
    after: UploadFile = File(...),
):
    """
    Accept two videos: 'before' and 'after'.
    Run MediaPipe on each, generate CSVs, and return a ZIP.
    """

    temp_dir = tempfile.mkdtemp(prefix="mp4_to_csv_")

    try:
        # Save uploaded files to temp dir
        before_path = os.path.join(temp_dir, "before.mp4")
        after_path = os.path.join(temp_dir, "after.mp4")

        with open(before_path, "wb") as f:
            f.write(await before.read())

        with open(after_path, "wb") as f:
            f.write(await after.read())

        # Output CSV paths
        before_csv = os.path.join(temp_dir, "before_angles.csv")
        after_csv = os.path.join(temp_dir, "after_angles.csv")

        # Run MediaPipe processing
        process_video(before_path, before_csv)
        process_video(after_path, after_csv)

        # Create ZIP of both CSVs
        zip_path = os.path.join(temp_dir, "angles.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(before_csv, arcname="before_angles.csv")
            zipf.write(after_csv, arcname="after_angles.csv")

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename="angles.zip",
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        # Clean up temp files after response is sent
        # (Render ephemeral disk, but good hygiene)
        shutil.rmtree(temp_dir, ignore_errors=True)
