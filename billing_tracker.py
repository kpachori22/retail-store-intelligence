from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

# Billing counter area
BILLING_ZONE = {
    "x1": 50,
    "y1": 180,
    "x2": 600,
    "y2": 850
}

zone_state = {}
zone_entry_time = {}

ZONES = {
    "BILLING_ZONE": BILLING_ZONE
}

unique_ids = set()
qualified_visitors = set()
dwell_times = []

# Get actual FPS
video = cv2.VideoCapture("CAM 5 - billing.mp4")

fps = video.get(cv2.CAP_PROP_FPS)

if fps == 0:
    fps = 30

video.release()

print(f"Video FPS: {fps:.2f}")


def get_zone(x, y):

    for zone_name, zone in ZONES.items():

        if (
            zone["x1"] <= x <= zone["x2"]
            and
            zone["y1"] <= y <= zone["y2"]
        ):
            return zone_name

    return None


results = model.track(
    source="CAM 5 - billing.mp4",
    tracker="bytetrack.yaml",
    stream=True,
    persist=True,
    conf=0.3,
    classes=[0],
    verbose=False
)

frame_count = 0

for result in results:

    frame_count += 1

    if result.boxes.id is None:
        continue

    boxes = result.boxes.xyxy.cpu().numpy()
    ids = result.boxes.id.cpu().numpy()

    for box, track_id in zip(boxes, ids):

        track_id = int(track_id)

        unique_ids.add(track_id)

        x1, y1, x2, y2 = box

        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        current_zone = get_zone(center_x, center_y)

        previous_zone = zone_state.get(track_id)

        # First time entering zone
        if previous_zone is None and current_zone:

            zone_state[track_id] = current_zone
            zone_entry_time[track_id] = frame_count

        # Visitor left billing zone
        elif previous_zone and current_zone is None:

            entry_frame = zone_entry_time[track_id]

            dwell_seconds = (
                frame_count - entry_frame
            ) / fps

            # Billing dwell threshold
            if 5 <= dwell_seconds <= 120:

                qualified_visitors.add(track_id)
                dwell_times.append(dwell_seconds)

                print(
                    f"VIS_{track_id} "
                    f"{previous_zone} "
                    f"DWELL={dwell_seconds:.1f}s"
                )

            del zone_state[track_id]
            del zone_entry_time[track_id]


# Handle visitors still inside zone at video end
for track_id in list(zone_state.keys()):

    entry_frame = zone_entry_time[track_id]

    dwell_seconds = (
        frame_count - entry_frame
    ) / fps

    if 5 <= dwell_seconds <= 300:

        qualified_visitors.add(track_id)
        dwell_times.append(dwell_seconds)

        print(
            f"VIS_{track_id} "
            f"BILLING_ZONE "
            f"DWELL={dwell_seconds:.1f}s "
            f"(still in zone at video end)"
        )

print("\n========== RESULTS ==========")

print(
    f"Total Tracks Detected: "
    f"{len(unique_ids)}"
)

print(
    f"Meaningful Billing Visitors: "
    f"{len(qualified_visitors)}"
)

if dwell_times:

    avg_dwell = sum(dwell_times) / len(dwell_times)

    print(
        f"Average Dwell Time: "
        f"{avg_dwell:.1f} sec"
    )

print("=============================")