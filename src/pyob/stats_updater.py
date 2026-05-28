import json

from pyob.dashboard_server import fetch_api


class StatsUpdater:
    def update_stats(self):
        try:
            response = fetch_api("/api/status")
            data = response.json()
            return data
        except Exception as e:
            print(f"Error updating stats: {e}")
            return None

    def update_pending_patches(self):
        try:
            response = fetch_api("/api/pending_patches")
            data = response.json()
            return data
        except Exception as e:
            print(f"Failed to fetch pending patches: {e}")
            return None

    def review_patch(self, patch_id, action):
        try:
            fetch_api(
                "/api/review_patch",
                method="POST",
                data=json.dumps({"patch_id": patch_id, "action": action}),
            )
        except Exception as e:
            print(f"Failed to {action} patch {patch_id}: {e}")

    def save_memory(self, memory_content):
        try:
            fetch_api(
                "/api/update_memory",
                method="POST",
                data=json.dumps({"content": memory_content}),
            )
        except Exception as e:
            print(f"Failed to save Logic Memory: {e}")

    def add_cascade_item(self, item):
        try:
            fetch_api(
                "/api/cascade_queue/add", method="POST", data=json.dumps({"item": item})
            )
        except Exception as e:
            print(f"Failed to add item to cascade queue: {e}")

    def move_queue_item(self, item_id, direction):
        try:
            fetch_api(
                "/api/cascade_queue/move",
                method="POST",
                data=json.dumps({"item_id": item_id, "direction": direction}),
            )
        except Exception as e:
            print(f"Failed to move item {item_id} {direction}: {e}")

    def remove_queue_item(self, item_id):
        try:
            fetch_api(
                "/api/cascade_queue/remove",
                method="POST",
                data=json.dumps({"item_id": item_id}),
            )
        except Exception as e:
            print(f"Failed to remove item {item_id}: {e}")