import numpy as np
from pathlib import Path


class OsnetExtractor:
    """
    Torchreid-free ReID extractor.

    Current backend:
    - torchvision MobileNetV3 Large by default
    - optional local weights: mobilenet_v3_large.pth
    - L2-normalized embedding
    """

    def __init__(self, model_name="mobilenet_v3_large", device=None, weights_path=None):
        self.model_name = model_name
        self.device = device
        self.weights_path = weights_path
        self.model = None
        self.transforms = None

    def _resolve_path(self, path):
        if not path:
            return None

        p = Path(path)
        if p.is_absolute():
            return p

        project_root = Path(__file__).resolve().parents[2]
        return project_root / p

    def _lazy_load(self):
        if self.model is not None:
            return

        import torch
        from torchvision.models import (
            mobilenet_v3_small,
            mobilenet_v3_large,
            MobileNet_V3_Small_Weights,
            MobileNet_V3_Large_Weights,
            resnet18,
            ResNet18_Weights,
        )

        if self.device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        model_name = (self.model_name or "mobilenet_v3_large").lower()

        if model_name in ["resnet18", "resnet_18"]:
            weights = ResNet18_Weights.DEFAULT
            model = resnet18(weights=None)
            model.fc = torch.nn.Identity()
            self.transforms = weights.transforms()
        elif model_name in ["mobilenet_v3_small", "mobilenetv3_small"]:
            weights = MobileNet_V3_Small_Weights.DEFAULT
            model = mobilenet_v3_small(weights=None)
            model.classifier = torch.nn.Identity()
            self.transforms = weights.transforms()
        else:
            weights = MobileNet_V3_Large_Weights.DEFAULT
            model = mobilenet_v3_large(weights=None)
            model.classifier = torch.nn.Identity()
            self.transforms = weights.transforms()

        local_weights = self._resolve_path(self.weights_path)
        if local_weights and local_weights.exists():
            state = torch.load(local_weights, map_location=self.device)

            # If saved full classifier model weights, load with strict=False
            # because classifier was replaced with Identity.
            missing, unexpected = model.load_state_dict(state, strict=False)
            print(f"Loaded ReID weights: {local_weights}")
        else:
            # Fallback: download torchvision weights automatically.
            if model_name in ["resnet18", "resnet_18"]:
                weights = ResNet18_Weights.DEFAULT
                model = resnet18(weights=weights)
                model.fc = torch.nn.Identity()
                self.transforms = weights.transforms()
            elif model_name in ["mobilenet_v3_small", "mobilenetv3_small"]:
                weights = MobileNet_V3_Small_Weights.DEFAULT
                model = mobilenet_v3_small(weights=weights)
                model.classifier = torch.nn.Identity()
                self.transforms = weights.transforms()
            else:
                weights = MobileNet_V3_Large_Weights.DEFAULT
                model = mobilenet_v3_large(weights=weights)
                model.classifier = torch.nn.Identity()
                self.transforms = weights.transforms()

        self.model = model.to(self.device)
        self.model.eval()

    def extract(self, image_bgr):
        self._lazy_load()

        import torch
        import cv2
        from PIL import Image

        if image_bgr is None or image_bgr.size == 0:
            return None

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        tensor = self.transforms(pil_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            feat = self.model(tensor)

        vec = feat.squeeze(0).detach().cpu().numpy().astype("float32")
        norm = np.linalg.norm(vec) + 1e-8
        return vec / norm
