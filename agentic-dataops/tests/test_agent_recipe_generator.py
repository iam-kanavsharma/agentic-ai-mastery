import json

from agent.agent_recipe_generator import generate_recipe_from_prompt


class MockLLM:
    def __init__(self, text: str):
        self.text = text

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0):
        return self.text


def test_generate_recipe_from_mock_llm():
    sample = {
        "select": ["order_id", "date", "region", "revenue"],
        "derive": [{"name": "date_day", "expr": "pd.to_datetime(df['date']).dt.date.astype(str)"}]
    }
    raw = json.dumps(sample)
    llm = MockLLM(raw)
    recipe = generate_recipe_from_prompt("Create daily revenue by region", llm)
    assert isinstance(recipe, dict)
    assert recipe["select"][0] == "order_id"
    assert recipe["derive"][0]["name"] == "date_day"
