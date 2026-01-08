import unittest
from unittest.mock import MagicMock
from agent.reviewer_agent import ReviewerAgent, ReviewResult

class TestReviewerAgent(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.agent = ReviewerAgent(llm=self.mock_llm)

    def test_approve_valid_recipe(self):
        # Mock LLM approving response
        self.mock_llm.generate.return_value = '{"approved": true, "feedback": "Looks good."}'
        
        recipe = {"select": ["col1"], "groupby": {"by": ["col1"], "agg": {"rev": "sum"}}}
        result = self.agent.review_recipe("Sum revenue by col1", recipe)
        
        self.assertTrue(result.approved)
        self.assertEqual(result.feedback, "Looks good.")

    def test_reject_bad_recipe(self):
        # Mock LLM rejecting response
        self.mock_llm.generate.return_value = '{"approved": false, "feedback": "Missing groupby key"}'
        
        recipe = {"select": ["col1"]} # Invalid for aggregation
        result = self.agent.review_recipe("Sum revenue by col1", recipe)
        
        self.assertFalse(result.approved)
        self.assertIn("Missing", result.feedback)

    def test_handle_invalid_json_response(self):
        # Mock LLM returning garbage
        self.mock_llm.generate.return_value = 'I think it is bad.' # No JSON
        
        recipe = {}
        result = self.agent.review_recipe("prompt", recipe)
        
        self.assertFalse(result.approved)
        self.assertIn("Reviewer Error", result.feedback)

if __name__ == '__main__':
    unittest.main()
