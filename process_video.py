import cv2
import mediapipe as mp
import numpy as np
import pandas as pd


mp_pose = mp.solutions.pose


def _angle_between_points(a, b, c):
    """
    Compute the angle ABC (in degrees) given three points:
    a, b, c are (x, y, z) numpy arrays.
    """
    ba = a - b
    bc = c - b

    # Normalize
    ba_norm = ba / (np.linalg.norm(ba) + 1e-8)
    bc_norm = bc / (np.linalg.norm(bc) + 1e-8)

    # Cosine of angle
    cos_angle = np.clip(np.dot(ba_norm, bc_norm), -1.0, 1.0)
    angle = np.degrees(np.arccos(cos_angle))
    return angle


def process_video(input_path: str, output_csv_path: str):
    """
    Run MediaPipe Pose on a video, compute a few joint angles per frame,
    and save them as a CSV.

    - input_path: path to the input MP4
    - output_csv_path: where to write the CSV
    """

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {input_path}")

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    rows = []
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR (OpenCV) to RGB (MediaPipe)
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            if not results.pose_landmarks:
                frame_idx += 1
                continue

            landmarks = results.pose_landmarks.landmark

            # Helper to get (x, y, z) as numpy array
            def p(idx):
                lm = landmarks[idx]
                return np.array([lm.x, lm.y, lm.z], dtype=np.float32)

            # Common indices (MediaPipe Pose)
            # https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
            LEFT_SHOULDER = 11
            LEFT_ELBOW = 13
            LEFT_WRIST = 15

            RIGHT_SHOULDER = 12
            RIGHT_ELBOW = 14
            RIGHT_WRIST = 16

            LEFT_HIP = 23
            LEFT_KNEE = 25
            LEFT_ANKLE = 27

            RIGHT_HIP = 24
            RIGHT_KNEE = 26
            RIGHT_ANKLE = 28

            # Compute some example angles
            try:
                left_elbow_angle = _angle_between_points(
                    p(LEFT_SHOULDER), p(LEFT_ELBOW), p(LEFT_WRIST)
                )
                right_elbow_angle = _angle_between_points(
                    p(RIGHT_SHOULDER), p(RIGHT_ELBOW), p(RIGHT_WRIST)
                )
                left_knee_angle = _angle_between_points(
                    p(LEFT_HIP), p(LEFT_KNEE), p(LEFT_ANKLE)
                )
                right_knee_angle = _angle_between_points(
                    p(RIGHT_HIP), p(RIGHT_KNEE), p(RIGHT_ANKLE)
                )
            except Exception:
                # If any landmark is missing or weird, skip this frame
                frame_idx += 1
                continue

            rows.append(
                {
                    "frame": frame_idx,
                    "left_elbow_deg": left_elbow_angle,
                    "right_elbow_deg": right_elbow_angle,
                    "left_knee_deg": left_knee_angle,
                    "right_knee_deg": right_knee_angle,
                }
            )

            frame_idx += 1

    finally:
        cap.release()
        pose.close()

    df = pd.DataFrame(rows)
    df.to_csv(output_csv_path, index=False)
