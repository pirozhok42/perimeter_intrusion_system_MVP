# ReID backend

This version does NOT use torchreid.

Current extractor:
- `app/reid/osnet_extractor.py`
- backend: torchvision MobileNetV3 Large by default
- weights file: `mobilenet_v3_large.pth` in project root

Config example:

```json
"reid": {
  "enabled": true,
  "model_name": "mobilenet_v3_large",
  "weights": "mobilenet_v3_large.pth",
  "similarity_threshold": 0.72,
  "device": "cuda"
}
```

Download models:

```bash
python tools/download_models.py
```
