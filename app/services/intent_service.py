import json
from typing import List, Dict
from openai import OpenAI
from app.core.config import settings

class IntentService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def analyze(self, requirement_content: str) -> List[Dict]:
        """
        Analyzes the requirement content to identify testing intents.
        """
        prompt = f"""
        Analyze the following requirement document and identify the key testing intents.
        A testing intent is a high-level goal or objective for testing, such as "verifying a core function", "testing for a specific type of error", or "checking performance under load".

        For each intent, provide a short description and categorize its scope (e.g., "functional", "performance", "security", "exception").

        Format the output as a single JSON object with a key "intents".
        - "intents": A list of objects, each with "description" and "scope".

        Example Output:
        {{
          "intents": [
            {{"description": "Verify that users can successfully log in with valid credentials.", "scope": "functional"}},
            {{"description": "Test how the system handles login attempts with invalid passwords.", "scope": "exception"}},
            {{"description": "Assess the login response time under high user concurrency.", "scope": "performance"}}
          ]
        }}

        Requirement Content:
        ---
        {requirement_content}
        ---
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        return extracted_data.get("intents", [])

