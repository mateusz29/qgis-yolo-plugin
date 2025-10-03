from ultralytics import YOLO

DATASET_YAML = "dataset/ShipRSImageNet.yaml"


def train_yolo_model():
    MODEL_NAME = "pretrained_models/yolo1s.pt"

    EPOCHS = 100
    BATCH_SIZE = 16
    IMAGE_SIZE = 800
    PATIENCE = 10

    model = YOLO(MODEL_NAME)

    _ = model.train(
        data=DATASET_YAML,
        imgsz=IMAGE_SIZE,
        epochs=EPOCHS,
        batch=BATCH_SIZE,
        patience=PATIENCE,
    )


def test_yolo_model():
    model = YOLO("../models/ships_yolo11s_best.pt")

    _ = model.val(data=DATASET_YAML, split="test", name="test", softnms=True)


if __name__ == "__main__":
    # train_yolo_model()
    test_yolo_model()
