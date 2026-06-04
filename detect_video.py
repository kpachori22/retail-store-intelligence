from ultralytics import YOLO

model = YOLO("yolov8n.pt")

results = model(
    "CAM 2.mp4",
    save=True
)

print("Video processing completed!")