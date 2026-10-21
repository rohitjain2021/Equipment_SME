# Setup, deployment, and local startup

Commands below use **Windows PowerShell**. Run them from the project root
(`Equipment_SME`) unless stated otherwise. Replace placeholders before use.

## 1. Install prerequisites

- Git and Python 3.13 (or another version supported by Streamlit).
- For backend deployment only: Node.js 22 LTS, AWS CLI v2, an AWS account with
  deployment permissions, and a Serverless Framework account.
- Amazon Nova Pro must be available to your AWS account in `us-east-1`.

Check your installations:

```powershell
git --version
python --version
# Needed only if deploying the backend:
node --version
npm --version
aws --version
```

## 2. Clone the repository

```powershell
git clone https://github.com/rohitjain2021/Equipment_SME.git
cd Equipment_SME
```

If already cloned, open a terminal in that existing project folder instead.

## 3. Create the Python environment and install packages

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\Streamlit_UI\requirements.txt
```

These commands install Streamlit and Requests inside `.venv`. Activation is
unnecessary because every command uses that environment's Python explicitly.
The deployed Lambda uses the AWS SDK included in its Python 3.13 runtime.

## 4. Get a backend URL or deploy your own

If the project owner has supplied a backend URL, skip to step 5.

### Configure AWS access

Use an existing AWS CLI profile when available. If you need to create the
`default` profile using access keys, configure it locally:

```powershell
aws configure --profile default
```

Enter credentials only at the local prompts and choose `us-east-1` as the region.
For an organization using IAM Identity Center, use its SSO profile instead.
Verify the profile and check the returned account locally:

```powershell
aws sts get-caller-identity --profile default
```

The deployment identity needs permissions for CloudFormation, Lambda, API
Gateway, IAM, CloudWatch Logs, and deployment artifacts in S3, plus any Framework
deployment support services. Runtime Lambda permissions are defined separately
in `serverless.yml`. Verify Nova Pro model access in Amazon Bedrock.

### Install Serverless Framework and sign in

```powershell
npm install --global serverless@4
serverless --version
serverless login
```

Complete the browser flow and wait for the terminal to confirm the sign-in.
Being signed into the website alone does not authenticate the CLI. Framework v4
requires authentication; check its licensing terms for your organization.

### Review, package, and deploy

```powershell
serverless print --stage Prod --aws-profile default
serverless package --stage Prod --aws-profile default
serverless deploy --stage Prod --aws-profile default
serverless info --stage Prod --aws-profile default
```

For a different AWS profile, replace `default` consistently in these commands.
Packaging produces deployment artifacts in `.serverless` and can provision
Framework deployment support resources. Deployment creates or updates stack
`equipment-sme-Prod` in `us-east-1`, including Lambda, a regional REST API, an IAM
role, and logs. It does not import existing manually created resources.

Copy the POST endpoint from the deployment output privately. It has this shape:

```text
https://<API_ID>.execute-api.us-east-1.amazonaws.com/Prod/
```

Use the root `/Prod/` endpoint, not `/Prod/sme_assistant`. The API waits up to
29 seconds even though Lambda's configured timeout is 123 seconds.

## 5. Configure and start the local server

In the same PowerShell terminal, from the project root:

```powershell
$env:SME_API_URL = 'https://<API_ID>.execute-api.us-east-1.amazonaws.com/Prod/'
.\.venv\Scripts\python.exe -m streamlit run .\Streamlit_UI\streamlit_app.py
```

Replace `<API_ID>` with the supplied or newly deployed API ID. Open
**http://localhost:8501**, paste equipment logs, and select **Summarize**.
The frontend needs no AWS credentials for the current API. Each analysis calls
the deployed AWS backend; it is not offline inference.

## 6. Stop and restart

Press `Ctrl+C` in the terminal to stop the server. To restart in a new terminal,
return to the project root and repeat step 5. The environment variable is scoped
to the terminal session. Package installation is needed only for initial setup
or when dependencies change.

To deploy backend code or infrastructure changes, run again from the project root:

```powershell
serverless deploy --stage Prod --aws-profile default
```

## 7. Host the frontend on Streamlit Community Cloud

The AWS backend must already be deployed. Community Cloud hosts the Streamlit
frontend and calls that backend; it does not deploy `serverless.yml`. No local
virtual environment, AWS CLI, or Serverless installation is needed on the host.

### Push the prepared files to GitHub

From the project root, review and publish the frontend and documentation:

```powershell
git status --short
git add .gitignore README.md SETUP_GUIDE.md architecture.svg Streamlit_UI/streamlit_app.py Streamlit_UI/requirements.txt
git diff --cached --stat
git diff --cached
git commit -m "Prepare Streamlit frontend for Community Cloud"
git push origin main
```

Review the staged diff before committing. If you are working on another branch,
push and select that branch instead. Confirm that the selected GitHub branch
contains `Streamlit_UI/streamlit_app.py` and `Streamlit_UI/requirements.txt`.
Do not upload virtual environments, `.serverless/`, or actual secret files.

### Create the hosted app

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) and connect your
   GitHub account, granting access to this repository.
2. Select **Create app**, then the option to deploy an existing app from GitHub.
3. Set these fields:

   | Field | Value |
   | --- | --- |
   | Repository | `rohitjain2021/Equipment_SME` |
   | Branch | `main` (or the branch you pushed) |
   | Main file path | `Streamlit_UI/streamlit_app.py` |
   | App URL | Choose an available subdomain, or accept the generated one |

4. Open **Advanced settings** and select Python **3.13**.
5. In **Secrets**, paste this TOML with your actual deployed API URL:

   ```toml
   SME_API_URL = "https://<API_ID>.execute-api.us-east-1.amazonaws.com/Prod/"
   ```

   Keep this key at the root level, without a `[section]` header. Streamlit
   exposes root-level secrets as environment variables, so the current
   `os.environ.get("SME_API_URL")` code works without modification. No AWS keys
   are required for the current API. Enter the real URL only in app settings.
6. Save the settings and deploy. Community Cloud discovers the requirements
   beside the entrypoint file, installs them, and starts the Streamlit server.
7. Open the generated `https://<app-name>.streamlit.app` URL and test **Summarize**
   with synthetic equipment logs. Confirm relevant findings appear (up to five),
   and that input without a meaningful equipment description shows a validation message.

Set secrets through the hosted app's settings; do not commit them to GitHub.
If you use a local `.streamlit/secrets.toml`, it is excluded by `.gitignore`.

### Update and share

Push future frontend changes to the selected branch to update the hosted app.
Use app settings to update secrets, and check the app logs if deployment fails.
AWS backend changes still require a separate `serverless deploy`.

Choose the intended viewer access in Community Cloud before sharing the URL.
Making the frontend private does not add authentication to the existing public
AWS API. Each submitted analysis still incurs AWS usage charges.

Official references: [Deploy your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
[dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies),
and [secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management).

## Common errors

| Problem | Fix |
| --- | --- |
| `No module named requests` or `streamlit` | Install requirements and use `.\.venv\Scripts\python.exe`, not system Python. |
| UI says the service is not configured | Locally, set `SME_API_URL` in the same terminal; on Community Cloud, add it as a root-level secret in app settings. |
| Community Cloud cannot find the app or dependencies | Verify the selected GitHub branch contains the main file and `requirements.txt` in `Streamlit_UI/`. |
| `serverless` is not recognized | Install the CLI and reopen the terminal if PATH changed. |
| Framework asks you to sign in | Run `serverless login` and wait for confirmation in the terminal. |
| AWS credentials or permissions error | Check the profile identity and its deployment permissions. |
| API returns 403 or missing authentication token | Check the API ID, region, exact stage capitalization, and root URL. |
| API returns 504 | The 29-second integration timeout was exceeded; inspect CloudWatch logs. |
| Port 8501 is already in use | Stop the previous server or append `--server.port 8502` and open that port. |

Do not commit credentials, tokens, account-specific output, or live API URLs.
The API is currently unauthenticated; hiding its URL does not enforce access
control. Local frontend startup does not publish a public website.
