import json
import uuid
from typing import List, Dict
from openai import OpenAI
from app.core.config import settings
from app.services.retrieval_service import RetrievalService

class GenerationService:
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def _create_plan(self, requirement_content: str, target_description: str, context: List[Dict]) -> List[str]:
        """
        Planner: Creates a test plan using LLM.
        """
        context_str = json.dumps(context, indent=2)
        prompt = f"""
        As a test manager, create a high-level test plan based on the requirement, user's target, and the provided context.
        The plan should be a list of key aspects to test.

        Requirement: {requirement_content}
        Target: {target_description}
        Context from Knowledge Base:
        {context_str}

        Output the plan as a JSON list of strings.
        Example: ["Test with valid credentials", "Test with invalid password", "Test password recovery flow"]
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        plan = json.loads(response.choices[0].message.content)
        return plan.get("plan", [])

    def _execute_plan(self, plan: List[str], context: List[Dict]) -> List[Dict]:
        """
        Executor: Generates detailed test cases for each step in the plan.
        """
        test_cases = []
        context_str = json.dumps(context, indent=2)

        for i, step in enumerate(plan):
            prompt = f"""
            As a test engineer, write a detailed test case for the following test plan item.
            
            Test Plan Item: "{step}"

            Relevant Context:
            {context_str}

            Format the output as a single JSON object with keys: "title", "preconditions", "steps", "expected_results".
            - "steps" should be a list of strings.
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            
            test_case_data = json.loads(response.choices[0].message.content)
            test_case_data["id"] = f"TC-{uuid.uuid4().hex[:6].upper()}"
            test_cases.append(test_case_data)
            
        return test_cases

    def generate_test_cases(self, requirement_content: str, target_description: str) -> List[Dict]:
        """
        Orchestrates the Planner-Executor process.
        """
        # 1. Retrieve context
        context = self.retrieval_service.search(query_text=target_description, top_k=5)

        # 2. Planner phase
        plan = self._create_plan(requirement_content, target_description, context)
        if not plan:
            return []

        # 3. Executor phase
        test_cases = self._execute_plan(plan, context)
        
        return test_cases
