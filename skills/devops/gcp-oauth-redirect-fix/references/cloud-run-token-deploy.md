# Cloud Run Token Deployment

How to deploy Google OAuth token to Cloud Run (where filesystem is ephemeral).

## Token Encoding

Cloud Run env vars don't handle JSON with special characters well. Use base64:

```bash
TOKEN_B64=$(cat ~/.hermes/google_token.json | base64 -w0)
echo "GOOGLE_TOKEN_B64: $TOKEN_B64" > /tmp/cloudrun_env.yaml
```

## Env Var Format

The YAML file for `--env-vars-file`:
```yaml
GOOGLE_TOKEN_B64: <base64 string>
```

NOT a nested dict — must be a flat string value.

## Deploy Command

```bash
# First deploy the service
gcloud run deploy mindcoach --source=. --region=us-central1 \
  --allow-unauthenticated --memory=512Mi --project=PROJECT_ID

# Then update with token env var
gcloud run services update mindcoach --region=us-central1 \
  --env-vars-file=/tmp/cloudrun_env.yaml --project=PROJECT_ID
```

## Code Reader

The code in `chat_api.py` reads the token from three sources (priority order):
1. File: `~/.hermes/google_token.json` (local development)
2. Env: `GOOGLE_TOKEN` (direct JSON string — may break on special chars)
3. Env: `GOOGLE_TOKEN_B64` (base64-encoded — preferred for Cloud Run)

```python
if os.path.exists(token_path):
    token_data = json.loads(Path(token_path).read_text())
elif os.environ.get('GOOGLE_TOKEN'):
    token_data = json.loads(os.environ['GOOGLE_TOKEN'])
elif os.environ.get('GOOGLE_TOKEN_B64'):
    import base64
    token_data = json.loads(base64.b64decode(os.environ['GOOGLE_TOKEN_B64']).decode())
```

## Dockerfile Note

Must use `python:3.11-slim` (glibc), NOT `nginx:alpine` (musl). Alpine can't load Google API Python packages.

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y nginx
RUN pip install google-api-python-client google-auth google-auth-oauthlib
```
