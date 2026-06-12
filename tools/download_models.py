from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
YOLO_MODEL_PATH = PROJECT_ROOT / "yolo11s.pt"
MOBILENET_MODEL_PATH = PROJECT_ROOT / "mobilenet_v3_large.pth"


def download_yolo11s():
    print("Downloading YOLO11s...")

    from ultralytics import YOLO

    # Ultralytics downloads model to cache/current working dir if missing.
    model = YOLO("yolo11s.pt")

    # Try to locate downloaded weights.
    candidate = Path("yolo11s.pt")
    if candidate.exists() and candidate.resolve() != YOLO_MODEL_PATH.resolve():
        shutil.copyfile(candidate, YOLO_MODEL_PATH)

    if not YOLO_MODEL_PATH.exists():
        # model.ckpt_path usually points to weights after loading
        ckpt_path = getattr(model, "ckpt_path", None)
        if ckpt_path and Path(ckpt_path).exists():
            shutil.copyfile(ckpt_path, YOLO_MODEL_PATH)

    if YOLO_MODEL_PATH.exists():
        print(f"YOLO11s saved: {YOLO_MODEL_PATH}")
    else:
        print("YOLO11s was loaded, but local file was not found. It may be stored in Ultralytics cache.")


def download_mobilenet_v3_large():
    print("Downloading MobileNetV3-Large...")

    import torch
    from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights

    weights = MobileNet_V3_Large_Weights.DEFAULT
    model = mobilenet_v3_large(weights=weights)

    torch.save(model.state_dict(), MOBILENET_MODEL_PATH)

    print(f"MobileNetV3-Large saved: {MOBILENET_MODEL_PATH}")


def main():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    download_yolo11s()
    download_mobilenet_v3_large()
    print("Done.")


if __name__ == "__main__":
    main()
