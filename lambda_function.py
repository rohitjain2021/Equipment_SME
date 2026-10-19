# 1. Import boto3 and create client connection with Bedrock
import boto3
import json

client_sme = boto3.client("bedrock-runtime")


def lambda_handler(event, context):

    # 2. Store the input in a variable and print it
    user_input = event["prompt"]
    print(user_input)

    # 3. Create user message
    message_prompt = [
        {
            "role": "user",
            "content": [
                {
                    "text": user_input
                }
            ]
        }
    ]

    # 4. System prompt
    system_prompt = [
        {
            "text": """
You are a wind turbine manufacturing operations assistant.

Analyze the provided equipment logs and return exactly 5 concise findings.

Formatting rules:
- Return exactly 5 bullet points.
- Put each bullet point on a new line.
- Start each bullet with "- ".
- Do not include any introduction, heading, conclusion, or extra commentary.
- Keep each bullet to one sentence.
- Prioritize incident details, equipment faults, component degradation, operational impact, downtime, and likely root cause.
- Include IDs, timestamps, measurements, downtime, and production loss when available.
- Do not repeat information.
- Do not invent missing details.

Required output format:
- Finding 1
- Finding 2
- Finding 3
- Finding 4
- Finding 5
"""
        }
    ]

    # 5. Model inference parameters
    inference_params = {
        "maxTokens": 500,
        "topP": 0.9,
        "topK": 20,
        "temperature": 0.2
    }

    # 6. Create request body
    request_body = {
        "schemaVersion": "messages-v1",
        "messages": message_prompt,
        "system": system_prompt,
        "inferenceConfig": inference_params
    }

    # 7. Invoke Amazon Nova through Bedrock
    response = client_sme.invoke_model(
        body=json.dumps(request_body),
        contentType="application/json",
        accept="application/json",
        modelId="amazon.nova-pro-v1:0",
        trace="ENABLED",
        # guardrailIdentifier="ilecfcii4uer",
        # guardrailVersion="1",
        performanceConfigLatency="standard"
    )

    # 8. Convert response body to dictionary
    response_dict = json.loads(response["body"].read())

    # 9. Extract generated text
    final_response = response_dict["output"]["message"]["content"][0]["text"]

    # 10. Return response
    return {
        "statusCode": 200,
        "body": json.dumps(final_response)
    }


# Documentation:
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/invoke_model.html
# https://docs.aws.amazon.com/nova/latest/userguide/using-invoke-api.html
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html