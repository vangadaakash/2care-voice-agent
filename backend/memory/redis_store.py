import json
import fakeredis

# For demonstration, we use fakeredis to simulate Redis without needing a server running.
redis_client = fakeredis.FakeStrictRedis(version=6)

class SessionMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        
    def get_context(self) -> dict:
        data = redis_client.get(f"session:{self.session_id}")
        if data:
            return json.loads(data)
        return {"intent": None, "doctor": None, "date": None, "time": None}
        
    def update_context(self, updates: dict):
        ctx = self.get_context()
        ctx.update(updates)
        # Set TTL to 1 hour (3600 seconds) as per bonus requirement
        redis_client.setex(f"session:{self.session_id}", 3600, json.dumps(ctx))
        
    def clear_context(self):
        redis_client.delete(f"session:{self.session_id}")
