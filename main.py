import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import zipfile

from process_video import process_video  # assumes this takes (input_mp4, output_csv)

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
async def upload_videos(before: UploadFile = File(...), after: UploadFile = File(...)):
    import uuid

    # Create a unique temp directory for this request
    temp_dir = f"/tmp/mp4_to_csv_{uuid.uuid4().hex}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Paths for saving uploaded videos
        before_path = os.path.join(temp_dir, "before.mp4")
        after_path = os.path.join(temp_dir, "after.mp4")

        # Save uploaded files
        with open(before_path, "wb") as f:
            f.write(await before.read())

        with open(after_path, "wb") as f:
            f.write(await after.read())

        print("Saved before video:", before_path)
        print("Saved after video:", after_path)

        # ---- PROCESS VIDEOS INTO CSVs ----
        before_csv_path = os.path.join(temp_dir, "before_angles.csv")
        after_csv_path = os.path.join(temp_dir, "after_angles.csv")

        try:
            process_video(before_path, before_csv_path)
            process_video(after_path, after_csv_path)
        except Exception as e:
            print("ERROR during video processing:", e)
            raise RuntimeError("Failed to process one of the videos")

        # ---- DEBUG CHECKS ----
        print("Before CSV exists:", os.path.exists(before_csv_path))
        print("After CSV exists:", os.path.exists(after_csv_path))

        if not os.path.exists(before_csv_path):
            raise RuntimeError("Before CSV was not created")

        if not os.path.exists(after_csv_path):
            raise RuntimeError("After CSV was not created")

        # ---- CREATE ZIP ----
        zip_path = os.path.join(temp_dir, "angles.zip")

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(before_csv_path, "before_angles.csv")
                zipf.write(after_csv_path, "after_angles.csv")
        except Exception as e:
            print("ERROR creating ZIP:", e)
            raise RuntimeError("Failed to create ZIP file")

        print("ZIP exists:", os.path.exists(zip_path))

        if not os.path.exists(zip_path):
            raise RuntimeError(f"ZIP file not created: {zip_path}")

        # ---- RETURN ZIP ----
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename="angles.zip",
        )

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
