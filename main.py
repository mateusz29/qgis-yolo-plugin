import gradio as gr
from ultralytics import YOLO

model = YOLO("models/YOLOv8l.pt")


def detect_object(image):
    results = model.predict(
        source=image,
        show_labels=True,
        show_conf=True,
    )

    return results[0].plot() if results else None


def main():
    iface = gr.Interface(
        fn=detect_object,
        inputs=gr.Image(type="numpy", label="Upload Image"),
        outputs=gr.Image(type="numpy", label="Result"),
        title="YOLOv8 Object Detection",
        description="Detect objects in images using YOLOv8.",
    )

    iface.launch()


if __name__ == "__main__":
    main()
