import os
import shutil
import uuid
import zipfile
from typing import List

from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure 'python-multipart' is in your requirements.txt
from process_video import process_video  # assumes this takes (input_mp4, output_csv)

app = FastAPI(title="Video to CSV Converter")

# Allow your Google Sites / other frontends to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
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
    background_tasks: BackgroundTasks,
    before: UploadFile = File(..., description="Upload the 'before' MP4 video"), 
    after: UploadFile = File(..., description="Upload the 'after' MP4 video")
):
    """
    Uploads two MP4 files, processes them into CSVs, 
    and returns a ZIP file. Cleans up temp files after download.
    """
    # Create a unique temp directory for this request
    temp_dir = f"/tmp/mp4_to_csv_{uuid.uuid4().hex}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Paths for saving uploaded videos
        before_path = os.path.join(temp_dir, "before.mp4")
        after_path = os.path.join(temp_dir, "after.mp4")

        # Save uploaded files in chunks to be memory-efficient
        for upload_file, destination in [(before, before_path), (after, after_path)]:
            with open(destination, "wb") as f:
                while content := await upload_file.read(1024 * 1024):  # 1MB chunks
                    f.write(content)

        # ---- PROCESS VIDEOS INTO CSVs ----
        before_csv_path = os.path.join(temp_dir, "before_angles.csv")
        after_csv_path = os.path.join(temp_dir, "after_angles.csv")

        # This runs your custom processing logic
        process_video(before_path, before_csv_path)
        process_video(after_path, after_csv_path)

        # ---- CREATE ZIP ----
        zip_path = os.path.join(temp_dir, "angles.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if os.path.exists(before_csv_path):
                zipf.write(before_csv_path, "before_angles.csv")
            if os.path.exists(after_csv_path):
                zipf.write(after_csv_path, "after_angles.csv")

        # Double check the zip exists before sending
        if not os.path.exists(zip_path):
            raise RuntimeError("Failed to create ZIP file.")

        # ---- CLEANUP & RETURN ----
        # background_tasks.add_task runs AFTER the response is sent
        background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename="angles.zip",
        )

    except Exception as e:
        # If something fails, attempt to clean up immediately and return error
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("UPLOAD ERROR:", e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )