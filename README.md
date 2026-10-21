# Equipment SME

A Streamlit app that summarizes wind turbine equipment logs into up to five
concise findings using **Amazon Nova Pro** (`amazon.nova-pro-v1:0`) on Amazon Bedrock.

Insufficient input such as `zdf` is rejected before inference. The model is
instructed to decline unrelated text and include only facts supported by the logs.

## Architecture

```text
Streamlit UI (local or Community Cloud) -> API Gateway -> Lambda -> Amazon Bedrock
```

![Equipment SME solution architecture](./architecture.svg)

The UI sends a JSON `prompt` to `POST /` on the API's `Prod` stage. API Gateway
maps it to `event["prompt"]`; Lambda calls Bedrock and returns the summary.
Infrastructure is defined in `serverless.yml` using Serverless Framework v4.

## Clone and run locally

Install Git and Python 3.13 or another Python version supported by Streamlit.
You also need a deployed backend URL, supplied by the project owner or obtained
by following the [setup and deployment guide](./SETUP_GUIDE.md).

Run these commands in **PowerShell**:

```powershell
git clone https://github.com/rohitjain2021/Equipment_SME.git
cd Equipment_SME
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\Streamlit_UI\requirements.txt
$env:SME_API_URL = 'https://<API_ID>.execute-api.us-east-1.amazonaws.com/Prod/'
.\.venv\Scripts\python.exe -m streamlit run .\Streamlit_UI\streamlit_app.py
```

Replace `<API_ID>` with your deployment's API ID. Open **http://localhost:8501**,
paste equipment logs, and select **Summarize**. Stop the server with `Ctrl+C`.
Start it through `python -m streamlit run`, not `python streamlit_app.py`.

No AWS credentials are needed to run the UI against the current unauthenticated
API. The UI runs locally; inference runs in AWS and incurs AWS usage charges.

## Backend deployment

Backend deployment needs an AWS CLI profile, Node.js 22 LTS, and Serverless
Framework v4 authentication. From the project root after setup:

```powershell
serverless deploy --stage Prod --aws-profile default
```

The first deployment creates the `equipment-sme-Prod` CloudFormation stack in
`us-east-1`; subsequent deployments update that stack. It does not automatically
adopt manually created resources. This deploys the backend, not frontend hosting.
See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for prerequisites, deployment, testing,
restarting the local server, and common errors.

## Host the frontend on Streamlit Community Cloud

Push the updated frontend and its `requirements.txt` to GitHub, then create an
app at [Streamlit Community Cloud](https://share.streamlit.io/). Select repository
`rohitjain2021/Equipment_SME`, branch `main`, and main file
`Streamlit_UI/streamlit_app.py`. In **Advanced settings**, select Python 3.13
and set the root-level secret `SME_API_URL` to your deployed backend URL.

Community Cloud installs the dependencies and provides a shareable
`https://<app-name>.streamlit.app` URL. The AWS backend stays in AWS. Follow
[step 7 in the setup guide](./SETUP_GUIDE.md#7-host-the-frontend-on-streamlit-community-cloud)
for the full publishing steps and the secrets format.

## Project files

| File | Purpose |
| --- | --- |
| `Streamlit_UI/streamlit_app.py` | Streamlit frontend for local or cloud hosting |
| `Streamlit_UI/requirements.txt` | Frontend Python dependencies |
| `lambda_function.py` | Lambda handler and Bedrock invocation |
| `serverless.yml` | Backend infrastructure and permissions |
| `SETUP_GUIDE.md` | Step-by-step setup and deployment commands |

Keep AWS credentials, Serverless tokens, and live API URLs out of documentation
and commits. The current API has no authentication; add an authorizer before
restricting access to approved users. Generated `.serverless` files and local
virtual environments are excluded from Git.
