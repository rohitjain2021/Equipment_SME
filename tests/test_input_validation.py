"""Run with: python -m unittest discover -s tests -v (no AWS calls)."""

import ast
import io
import json
from pathlib import Path
import re
import types
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
MESSAGE = "Please provide valid equipment logs describing an equipment condition or incident."


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.bedrock = Mock()
        self.bedrock.invoke_model.return_value = {
            "body": io.BytesIO(json.dumps({
                "output": {"message": {"content": [{"text": "- Motor failed."}]}}
            }).encode())
        }
        boto3 = types.ModuleType("boto3")
        boto3.client = Mock(return_value=self.bedrock)
        namespace = {}
        with patch.dict("sys.modules", {"boto3": boto3}):
            exec(compile((ROOT / "lambda_function.py").read_text(), "lambda_function.py", "exec"), namespace)
        self.handler = namespace["lambda_handler"]

        # Load only the API helper so these tests do not execute the Streamlit UI.
        tree = ast.parse((ROOT / "Streamlit_UI/streamlit_app.py").read_text(encoding="utf-8"))
        helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "summarize_logs")
        self.post = Mock()
        ui_namespace = {
            "json": json, "re": re, "API_URL": "https://example.invalid/Prod/",
            "requests": types.SimpleNamespace(post=self.post),
        }
        exec(compile(ast.Module(body=[helper], type_ignores=[]), "frontend_helper", "exec"), ui_namespace)
        self.summarize = ui_namespace["summarize_logs"]

    def test_invalid_backend_input_never_invokes_model(self):
        for event in ({}, None, [], {"prompt": None}, {"prompt": 123},
                      {"prompt": ""}, {"prompt": "   "}, {"prompt": "zdf"},
                      {"prompt": "123456"}, {"prompt": "!@#$"}):
            with self.subTest(event=event):
                response = self.handler(event, None)
                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(json.loads(response["body"])["error"], MESSAGE)
        self.bedrock.invoke_model.assert_not_called()

    def test_short_valid_log_is_forwarded_and_prompt_does_not_force_five(self):
        response = self.handler({"prompt": "  Motor failed.  "}, None)
        self.assertEqual(json.loads(response["body"]), "- Motor failed.")
        kwargs = self.bedrock.invoke_model.call_args.kwargs
        request = json.loads(kwargs["body"])
        self.assertEqual(request["messages"][0]["content"][0]["text"], "Motor failed.")
        self.assertIn("between 1 and 5", request["system"][0]["text"])
        self.assertIn("Missing downtime or production loss does not mean zero", request["system"][0]["text"])
        self.assertEqual(request["inferenceConfig"]["temperature"], 0.0)

    def test_gibberish_is_rejected_in_frontend_before_network_call(self):
        with self.assertRaisesRegex(ValueError, "Please provide valid equipment logs"):
            self.summarize("zdf")
        self.post.assert_not_called()

    def test_non_proxy_validation_error_is_shown_to_user(self):
        self.post.return_value.json.return_value = {
            "statusCode": 400, "body": json.dumps({"error": MESSAGE})
        }
        with self.assertRaisesRegex(ValueError, "Please provide valid equipment logs"):
            self.summarize("Motor failed.")

    def test_valid_summary_decodes_correctly(self):
        self.post.return_value.json.return_value = {
            "statusCode": 200, "body": json.dumps("- Motor failed.")
        }
        self.assertEqual(self.summarize("Motor failed."), "- Motor failed.")

    def test_model_insufficient_input_message_is_preserved(self):
        self.post.return_value.json.return_value = {
            "statusCode": 200, "body": json.dumps(MESSAGE)
        }
        self.assertEqual(self.summarize("hello how are you"), MESSAGE)


if __name__ == "__main__":
    unittest.main()
