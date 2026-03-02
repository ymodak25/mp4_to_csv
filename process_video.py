import csv

def process_video(input_path: str, output_path: str) -> None:
    """
    Replace this stub with your real MP4 -> CSV logic.

    Expected behavior:
      - Read the video at input_path
      - Run your MediaPipe / angle extraction
      - Write results to output_path as CSV
    """
    # TODO: replace this with your actual processing code.
    # This is just a placeholder so the backend runs.
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "angle1", "angle2"])
        writer.writerow([0, 0.0, 0.0])
