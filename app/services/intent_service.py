import json
import uuid
from typing import List, Dict
from openai import OpenAI
from app.core.config import settings
from app.core.prompts import PromptTemplates

class IntentService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def analyze(self, requirement_content: str) -> List[Dict]:
        """
        Analyzes the requirement content to identify testing intents.
        Returns a list of intents with intent_id, description, and scope.
        """
        prompt = PromptTemplates.get_intent_analysis_prompt(requirement_content)

        response = self.openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=settings.llm_temperature
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        intents = extracted_data.get("intents", [])

        # Add intent_id to each intent
        for intent in intents:
            intent['intent_id'] = f"INTENT-{uuid.uuid4().hex[:8].upper()}"

        return intents

