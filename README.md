# Equipment SME

## Architecture

The solution accepts a summarization request from the Equipment SME, sends it
through an API endpoint to an AWS Lambda function, and uses Amazon Bedrock to
generate the response.

![Equipment SME solution architecture](./architecture.svg)

### Request flow

1. The Equipment SME submits a **“Summarize text”** request.
2. Amazon API Gateway forwards the request to AWS Lambda as `event.prompt`.
3. Lambda combines the user prompt with a system prompt and calls Amazon
   Bedrock.
4. The generated summary returns to the Equipment SME through API Gateway.

### Components

| Component | Responsibility |
| --- | --- |
| Equipment SME | Submits the text and receives the summary. |
| Amazon API Gateway | Exposes the API and routes requests to Lambda. |
| AWS Lambda | Processes the request and invokes the model. |
| Amazon Bedrock | Generates a summary from the user and system prompts. |
