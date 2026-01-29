from typing import Dict, Any

# This is a temporary, in-memory data store to simulate a database.
# In a real production application, you would use a proper database like PostgreSQL or MySQL.

TEMP_REQUIREMENT_STORE: Dict[str, Dict[str, Any]] = {}

# Store for simulating async tasks
TEMP_TASK_STORE: Dict[str, Dict[str, Any]] = {}
