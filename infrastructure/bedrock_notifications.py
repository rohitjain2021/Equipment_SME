"""Publish one metadata-only SNS message per recorded Nova Pro invocation."""

import base64
import gzip
import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    payload = json.loads(gzip.decompress(base64.b64decode(event["awslogs"]["data"])))
    if payload.get("messageType") != "DATA_MESSAGE":
        return {"published": 0}

    client = boto3.client("sns")
    published = 0
    for log_event in payload.get("logEvents", []):
        # Invalid records fail the batch rather than silently losing an alert.
        record = json.loads(log_event["message"])
        if record.get("modelId") != os.environ["BEDROCK_MODEL_ID"]:
            continue
        message = {
            "event": "Bedrock model invocation recorded",
            "timestamp": record.get("timestamp"),
            "modelId": record["modelId"],
            "operation": record.get("operation"),
            "requestId": record.get("requestId"),
            "region": record.get("region"),
            "inputTokenCount": record.get("input", {}).get("inputTokenCount"),
            "outputTokenCount": record.get("output", {}).get("outputTokenCount"),
            "logEventId": log_event.get("id"),
            "note": "Usage notification, not an abuse determination. Log delivery can be delayed; retries can cause duplicate notifications.",
        }
        # Never email or log prompts, outputs, caller identities, or recipient details.
        client.publish(
            TopicArn=os.environ["ALERT_TOPIC_ARN"],
            Subject="Equipment SME: Bedrock invocation recorded",
            Message=json.dumps(message, indent=2),
        )
        logger.info("Invocation notification published; requestId=%s", record.get("requestId"))
        published += 1
    return {"published": published}
