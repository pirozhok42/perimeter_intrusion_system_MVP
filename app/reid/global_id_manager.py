import threading
import numpy as np


class GlobalIdManager:
    """
    Shared global ReID gallery.

    One instance must be reused across all tracking cameras while live processing is running.
    """

    def __init__(self, similarity_threshold=0.72):
        self.similarity_threshold = similarity_threshold
        self.next_global_id = 1
        self.gallery = {}
        self.lock = threading.Lock()

    def match(self, embedding):
        if embedding is None:
            return None, -1.0, False

        with self.lock:
            best_id = None
            best_score = -1.0

            for gid, stored_embedding in self.gallery.items():
                score = float(np.dot(embedding, stored_embedding))
                if score > best_score:
                    best_id = gid
                    best_score = score

            if best_id is not None and best_score >= self.similarity_threshold:
                updated = 0.85 * self.gallery[best_id] + 0.15 * embedding
                self.gallery[best_id] = updated / (np.linalg.norm(updated) + 1e-8)
                return best_id, best_score, False

            gid = self.next_global_id
            self.next_global_id += 1
            self.gallery[gid] = embedding
            return gid, best_score, True

    def update_existing(self, global_id, embedding):
        if embedding is None:
            return

        with self.lock:
            if global_id not in self.gallery:
                self.gallery[global_id] = embedding
                return

            updated = 0.90 * self.gallery[global_id] + 0.10 * embedding
            self.gallery[global_id] = updated / (np.linalg.norm(updated) + 1e-8)
