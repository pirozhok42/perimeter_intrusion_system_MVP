import argparse
import time
from app.config import AppConfig
from app.pipeline import PerimeterPipeline
from app.video.video_io import list_videos

def process_source(source, config_path):
    config = AppConfig.from_json(config_path)
    pipeline = PerimeterPipeline(config)
    videos = list_videos(source)

    if not videos:
        print(f"No videos found in {source}")
        return

    for video in videos:
        print(f"\nProcessing: {video}")
        result = pipeline.process_video(video)
        print("Done:")
        for k, v in result.items():
            print(f"  {k}: {v}")

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
        config = AppConfig.from_json(args.config)
        pipeline = PerimeterPipeline(config)
        videos = list_videos(args.source)

        for video in videos:
            key = str(video.resolve())
            if key in processed:
                continue
            print(f"\nNew video: {video}")
            result = pipeline.process_video(video)
            processed.add(key)
            print("Done:", result)

        time.sleep(args.poll_seconds)

if __name__ == "__main__":
    main()
