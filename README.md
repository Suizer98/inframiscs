# inframiscs

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11.11 (see `.python-version`).

```bash
uv sync
```

## Run AWS scripts

Upload local secrets to AWS Secrets Manager:

```bash
uv run python AWS/aws_secret_manager_create.py
```

Download tagged secrets from AWS:

```bash
uv run python AWS/aws_secret_manager_get.py
```

Or activate the venv first:

```bash
source .venv/bin/activate
python AWS/aws_secret_manager_create.py
python AWS/aws_secret_manager_get.py
```
