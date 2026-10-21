"""Manage regional Bedrock logging without overwriting another destination."""

import json
import logging
import time
import urllib.request

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def desired_config(properties):
    return {
        "cloudWatchConfig": {
            "logGroupName": properties["LogGroupName"],
            "roleArn": properties["RoleArn"],
        },
        "textDataDeliveryEnabled": True,
        "imageDataDeliveryEnabled": False,
        "embeddingDataDeliveryEnabled": False,
        "videoDataDeliveryEnabled": False,
        "audioDataDeliveryEnabled": False,
    }


def same_config(current, expected):
    """AWS may omit disabled modalities, so normalize their defaults."""
    if not current:
        return False
    normalized = dict(current)
    for key in expected:
        if key.endswith("DeliveryEnabled"):
            normalized.setdefault(key, False)
    return normalized == expected


def configure(event, client):
    target = desired_config(event["ResourceProperties"])
    current = client.get_model_invocation_logging_configuration().get("loggingConfig")
    operation = event["RequestType"]
    if operation == "Delete":
        if same_config(current, target):
            client.delete_model_invocation_logging_configuration()
        return
    if operation not in ("Create", "Update"):
        raise ValueError("Unsupported custom-resource operation")
    if same_config(current, target):
        return
    previous = event.get("OldResourceProperties")
    if current and not (operation == "Update" and previous and same_config(current, desired_config(previous))):
        raise ValueError("Another Bedrock invocation logging configuration already exists; refusing to overwrite it.")
    # Allow time for a newly created delivery role and policy to propagate.
    for attempt in range(4):
        try:
            client.put_model_invocation_logging_configuration(loggingConfig=target)
            return
        except ClientError as error:
            if error.response["Error"]["Code"] not in ("AccessDeniedException", "ValidationException") or attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))


def handler(event, context):
    status = "SUCCESS"
    reason = "Bedrock invocation logging configuration processed."
    try:
        client = boto3.client("bedrock", config=Config(
            connect_timeout=5, read_timeout=10, retries={"total_max_attempts": 1}
        ))
        configure(event, client)
        logger.info("Bedrock logging configuration operation completed: %s", event["RequestType"])
    except Exception as error:
        logger.exception("Bedrock logging configuration failed")
        status = "FAILED"
        reason = str(error)[:500]
    body = json.dumps({
        "Status": status,
        "Reason": reason,
        "PhysicalResourceId": event.get("PhysicalResourceId") or (
            event["StackId"].split("/")[1] + "-bedrock-invocation-logging"
        ),
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "NoEcho": True,
        "Data": {},
    }).encode("utf-8")
    # Never log the event: ResponseURL is a temporary signed credential.
    request = urllib.request.Request(event["ResponseURL"], data=body,
                                     headers={"Content-Type": ""}, method="PUT")
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()
