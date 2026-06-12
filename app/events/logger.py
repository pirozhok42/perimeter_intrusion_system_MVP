import json
import pandas as pd
from pathlib import Path

class EventLogger:
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(event)

    def save(self, csv_path, json_path):
        csv_path, json_path = Path(csv_path), Path(json_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.events).to_csv(csv_path, index=False)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
