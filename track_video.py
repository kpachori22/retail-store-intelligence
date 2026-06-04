from ultralytics import YOLO

model = YOLO("yolov8n.pt")

results = model.track(
    source="CAM 2.mp4",
    tracker="bytetrack.yaml",
    save=True,
    persist=True,
    conf=0.5
)

print("Tracking completed!")