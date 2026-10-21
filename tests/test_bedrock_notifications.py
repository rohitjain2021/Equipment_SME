"""Check per-invocation notification routing without AWS or email delivery."""

import base64
import gzip
import importlib.util
import json
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch


class BedrockNotificationTests(unittest.TestCase):
    def setUp(self):
        sdk = types.ModuleType("boto3")
        self.sns = Mock()
        sdk.client = Mock(return_value=self.sns)
        path = Path(__file__).resolve().parents[1] / "infrastructure/bedrock_notifications.py"
        spec = importlib.util.spec_from_file_location("tested_notifications", path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"boto3": sdk}):
            spec.loader.exec_module(self.module)
        self.environment = patch.dict("os.environ", {
            "ALERT_TOPIC_ARN": "test-topic", "BEDROCK_MODEL_ID": "amazon.nova-pro-v1:0"
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def event(self, records, message_type="DATA_MESSAGE"):
        data = {"messageType": message_type, "logEvents": [
            {"id": str(index), "message": json.dumps(record)}
            for index, record in enumerate(records)
        ]}
        return {"awslogs": {"data": base64.b64encode(gzip.compress(json.dumps(data).encode())).decode()}}

    def record(self):
        return {
            "modelId": "amazon.nova-pro-v1:0", "requestId": "test-request",
            "input": {"inputTokenCount": 10, "inputBodyJson": {"secret": "private-prompt"}},
            "output": {"outputTokenCount": 5, "outputBodyJson": {"text": "private-output"}},
            "identity": {"arn": "private-identity"},
        }

    def test_one_notification_per_invocation_in_batch(self):
        result = self.module.handler(self.event([self.record(), self.record()]), None)
        self.assertEqual(result["published"], 2)
        self.assertEqual(self.sns.publish.call_count, 2)

    def test_messages_include_tokens_but_not_content_or_identity(self):
        self.module.handler(self.event([self.record()]), None)
        args = self.sns.publish.call_args.kwargs
        self.assertEqual(args["TopicArn"], "test-topic")
        content = json.loads(args["Message"])
        self.assertEqual(content["inputTokenCount"], 10)
        for secret in ("private-prompt", "private-output", "private-identity"):
            self.assertNotIn(secret, args["Message"])

    def test_control_message_does_not_publish(self):
        self.assertEqual(self.module.handler(self.event([], "CONTROL_MESSAGE"), None), {"published": 0})
        self.module.boto3.client.assert_not_called()

    def test_other_model_does_not_publish(self):
        record = self.record()
        record["modelId"] = "amazon.nova-lite-v1:0"
        self.assertEqual(self.module.handler(self.event([record]), None), {"published": 0})
        self.sns.publish.assert_not_called()

    def test_publish_failure_propagates_for_retry(self):
        self.sns.publish.side_effect = RuntimeError("publish failed")
        with self.assertRaisesRegex(RuntimeError, "publish failed"):
            self.module.handler(self.event([self.record()]), None)

    def test_empty_batch_does_not_publish(self):
        self.assertEqual(self.module.handler(self.event([]), None), {"published": 0})
        self.sns.publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
