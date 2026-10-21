"""Regression checks for the account-level logging custom resource; no AWS calls."""

import importlib.util
import json
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch


class BedrockLoggingTests(unittest.TestCase):
    def setUp(self):
        sdk = types.ModuleType("boto3")
        config = types.ModuleType("botocore.config")
        config.Config = Mock()
        errors = types.ModuleType("botocore.exceptions")
        errors.ClientError = type("ClientError", (Exception,), {})
        modules = {"boto3": sdk, "botocore": types.ModuleType("botocore"),
                   "botocore.config": config, "botocore.exceptions": errors}
        path = Path(__file__).resolve().parents[1] / "infrastructure/bedrock_logging.py"
        spec = importlib.util.spec_from_file_location("tested_bedrock_logging", path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", modules):
            spec.loader.exec_module(self.module)
        self.client = Mock()
        self.client.get_model_invocation_logging_configuration.return_value = {}
        self.props = {"LogGroupName": "/test/logs", "RoleArn": "test-role"}
        self.event = {"RequestType": "Create", "ResourceProperties": self.props}

    def test_create_enables_text_only(self):
        self.module.configure(self.event, self.client)
        config = self.client.put_model_invocation_logging_configuration.call_args.kwargs["loggingConfig"]
        self.assertTrue(config["textDataDeliveryEnabled"])
        self.assertFalse(config["imageDataDeliveryEnabled"])
        self.assertNotIn("s3Config", config)

    def test_existing_unrelated_configuration_is_not_overwritten(self):
        self.client.get_model_invocation_logging_configuration.return_value = {
            "loggingConfig": {"s3Config": {"bucketName": "someone-elses-bucket"}}
        }
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            self.module.configure(self.event, self.client)
        self.client.put_model_invocation_logging_configuration.assert_not_called()

    def test_repeated_create_is_idempotent(self):
        target = self.module.desired_config(self.props)
        target.pop("audioDataDeliveryEnabled")
        self.client.get_model_invocation_logging_configuration.return_value = {"loggingConfig": target}
        self.module.configure(self.event, self.client)
        self.client.put_model_invocation_logging_configuration.assert_not_called()

    def test_update_accepts_owned_previous_configuration(self):
        self.event.update(RequestType="Update", OldResourceProperties=self.props)
        self.client.get_model_invocation_logging_configuration.return_value = {
            "loggingConfig": self.module.desired_config(self.props)
        }
        self.event["ResourceProperties"] = dict(self.props, LogGroupName="/test/new")
        self.module.configure(self.event, self.client)
        self.client.put_model_invocation_logging_configuration.assert_called_once()

    def test_delete_only_removes_owned_configuration(self):
        self.event["RequestType"] = "Delete"
        self.client.get_model_invocation_logging_configuration.return_value = {
            "loggingConfig": self.module.desired_config(self.props)
        }
        self.module.configure(self.event, self.client)
        self.client.delete_model_invocation_logging_configuration.assert_called_once()

    def test_delete_preserves_external_changes(self):
        self.event["RequestType"] = "Delete"
        self.client.get_model_invocation_logging_configuration.return_value = {"loggingConfig": {"s3Config": {}}}
        self.module.configure(self.event, self.client)
        self.client.delete_model_invocation_logging_configuration.assert_not_called()

    def test_failed_create_cleanup_does_not_remove_external_configuration(self):
        self.event["RequestType"] = "Delete"
        self.module.configure(self.event, self.client)
        self.client.delete_model_invocation_logging_configuration.assert_not_called()

    def test_handler_reports_failure_to_cloudformation(self):
        self.event.update(StackId="arn:example:stack/test-stack/id", RequestId="test", LogicalResourceId="Logging", ResponseURL="https://example.invalid/response")
        self.module.boto3.client = Mock(return_value=self.client)
        self.client.get_model_invocation_logging_configuration.side_effect = ValueError("test failure")
        with patch.object(self.module.urllib.request, "urlopen") as send, patch.object(self.module.logger, "exception"):
            self.module.handler(self.event, None)
        body = json.loads(send.call_args.args[0].data)
        self.assertEqual(body["Status"], "FAILED")
        self.assertEqual(body["PhysicalResourceId"], "test-stack-bedrock-invocation-logging")


if __name__ == "__main__":
    unittest.main()
