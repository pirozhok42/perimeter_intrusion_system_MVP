import argparse
import time
from pathlib import Path

from app.config import AppConfig
from app.pipeline import PerimeterPipeline
from app.video.video_io import list_videos, infer_camera_name_from_video


def resolve_config_for_video(video_path, source_root, default_config):
    camera_name = infer_camera_name_from_video(video_path, source_root)
    camera_config = Path("configs") / f"{camera_name}.json"
    if camera_config.exists():
        return str(camera_config)
    return default_config


def process_one_video(video, source_root, default_config):
    config_path = resolve_config_for_video(video, source_root, default_config)
    config = AppConfig.from_json(config_path)

    pipeline = PerimeterPipeline(config)
    result = pipeline.process_video(video)

    print("Done:")
    for k, v in result.items():
        print(f"  {k}: {v}")


def process_source(source, config_path):
    videos = list_videos(source)

    if not videos:
        print(f"No videos found in {source}")
        return

    for video in videos:
        print(f"\nProcessing: {video}")
        process_one_video(video, source, config_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--config", default="configs/camera_1.json")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=3.0)
    args = parser.parse_args()

    if not args.watch:
        process_source(args.source, args.config)
        return

    processed = set()
    print(f"Watching folder: {args.source}")

    while True:
        videos = list_videos(args.source)

        for video in videos:
            key = str(video.resolve())
            if key in processed:
                continue
            print(f"\nNew video: {video}")
            process_one_video(video, args.source, args.config)
            processed.add(key)

        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
