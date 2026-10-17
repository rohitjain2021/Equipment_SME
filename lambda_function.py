#1 Import boto3 and create client connection with bedrock
import boto3
import json
client_sme = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    #2 a. Store the input in a variable, b. print the event
    user_input = event['prompt']
    print(user_input)

    #3 Get request syntax details from documentation - (Inference, user & system prompt, schema version) & body should be json object - use json.dumps for body & print response
    message_prompt = [{"role": "user", "content": [{"text": user_input}]}]
    
    system_prompt = [
            {
                "text": "Act as a wind turbine manufacturing assistant. Summarize the logs in 5 lines"
            }
]

    inference_params = {"maxTokens": 2500, "topP": 0.9, "topK": 20, "temperature": 0.7}

    request_body = {
    "schemaVersion": "messages-v1",
    "messages": message_prompt,
    "system": system_prompt,
    "inferenceConfig": inference_params,
}
    
    
    response = client_sme.invoke_model(
        body=json.dumps(request_body),
        contentType='application/json',
        accept='application/json',
        modelId='amazon.nova-pro-v1:0',
        trace='ENABLED',
        #guardrailIdentifier='ilecfcii4uer',
        #guardrailVersion='1',
        performanceConfigLatency='standard',
    )

    #print(response)

    #4 Read the Streaming Body to Bytes (.read method) and then Bytes to Dictionary using json.loads
    response_dict = json.loads(response['body'].read())
    #print(response_dict)
    #print(type(response_dict))

    #5 Extract the text from the dictionary
    final_response = response_dict['output']['message']['content'][0]['text']
    #print(final_response)

    #6. Update the return statement to return the final response
    return {
        'statusCode': 200,
        'body': json.dumps(final_response)
    }




# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/invoke_model.html
# https://docs.aws.amazon.com/nova/latest/userguide/using-invoke-api.html
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html



