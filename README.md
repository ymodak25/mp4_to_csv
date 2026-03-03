# 🎥📊 mp4_to_csv
### Cloud-Based Biomechanical Data Extraction Pipeline

**mp4_to_csv** is a high-performance backend utility designed to bridge the gap between raw video footage and structured kinematic data. 
By leveraging **FastAPI** for asynchronous request handling and **MediaPipe** for state-of-the-art pose estimation, this tool allows researchers to upload "Before" and "After" performance videos and receive synchronized CSV angle logs in a single compressed package.

---

## 🔬 Research Objective

Extracting joint angles manually from video is a bottleneck in biomechanical research. This project provides a scalable, cloud-ready solution to:

- **Automate Joint Mapping:** Eliminate manual frame-by-frame angle calculations.
- **Synchronized Comparison:** Process pairwise video sets (e.g., pre-training vs. post-training) simultaneously.
- **Web Integration:** Provide a RESTful API that can be embedded into any frontend or research dashboard.

---

## 🛠 Tech Stack

- **Framework:** FastAPI (Python 3.10)
- **Computer Vision:** MediaPipe, OpenCV (Headless)
- **Data Science:** Pandas, NumPy
- **Deployment:** Render (Cloud PaaS)
- **Environment:** Docker-ready / Linux-compatible

---

## ▶️ How to Use the API

The backend is currently live and provides an interactive **Swagger UI** for testing and documentation.

### **1. Access the Interface**
Navigate to the live documentation page:
`https://mp4-to-csv-1.onrender.com/docs`

### **2. Upload & Process**
1. Click on the **POST `/upload`** endpoint.
2. Select **"Try it out"**.
3. Attach your `before.mp4` and `after.mp4` files.
4. Click **Execute**.

### **3. Download Results**
Once processing is complete, the API will return a **200 Success** response and a download link for `angles.zip`, containing:
- `before_angles.csv`
- `after_angles.csv`

---

## 📐 Data Structure

The generated CSV files contain a frame-by-frame breakdown of critical joint angles required for kinematic analysis:

| Landmark Group | Input Logic | Analysis Value |
| --- | --- | --- |
| **Knee Extension** | Hip-Knee-Ankle | Detects fatigue-based reach reduction. |
| **Shoulder Rotation** | Hip-Shoulder-Elbow | Monitors torso stability and guard positioning. |
| **Hip Flexion** | Shoulder-Hip-Knee | Measures core engagement and postural drift. |

---

## 🚀 Backend Workflow (Abstract)

The system utilizes an asynchronous pipeline to ensure data integrity during heavy processing:

### 1. **Secure Ingestion**
The API receives multipart form data. Files are streamed in 1MB chunks to the server's temporary storage to prevent memory spikes on cloud instances.

### 2. **MediaPipe Transformation**
The `process_video.py` module initializes a headless Pose instance. It iterates through every frame, calculating geometric vectors for key landmarks and handling missing frames via coordinate interpolation.

### 3. **Batch Archiving**
Once both CSVs are generated, the system packages them into a ZIP archive. 

### 4. **Automated Cleanup**
Utilizing **FastAPI BackgroundTasks**, the server automatically purges the temporary directory after the user completes the download, ensuring zero data footprint and maintaining server performance.

---

## 🗂️ mp4_to_csv Change-Log

### March - 2026
- **FastAPI Migration:** Transitioned from a local script to a production-ready Web API.
- **Cloud Deployment:** Successfully deployed to Render using a Python 3.10 environment.
- **Multi-File Handling:** Integrated ZIP compression to allow for batch processing of paired videos.
- **CORS Integration:** Enabled cross-origin requests to support embedding in Google Sites and other research frontends.

---
