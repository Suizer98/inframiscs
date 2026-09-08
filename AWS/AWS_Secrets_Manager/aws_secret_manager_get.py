import os

import boto3
from botocore.exceptions import ClientError

region_name = "ap-southeast-1"

client = boto3.client(
    "secretsmanager",
    region_name=region_name,
    aws_access_key_id="",
    aws_secret_access_key="",
)

script_dir = os.path.dirname(os.path.abspath(__file__))

secret_tags = [
    {"Key": "Environment", "Value": "DEV"},
    {"Key": "Application", "Value": "SCHEDULEDJOBS"},
]

tags_by_key = {tag["Key"]: tag["Value"] for tag in secret_tags}


def list_tagged_secret_names() -> list[str]:
    environment_tag_key = next(tag["Key"] for tag in secret_tags if tag["Key"] == "Environment")
    application_tag_key = next(tag["Key"] for tag in secret_tags if tag["Key"] == "Application")

    secret_names = []
    paginator = client.get_paginator("list_secrets")
    for page in paginator.paginate(
        Filters=[
            {"Key": "tag-key", "Values": [environment_tag_key]},
            {"Key": "tag-value", "Values": [tags_by_key[environment_tag_key]]},
        ]
    ):
        for secret in page.get("SecretList", []):
            tags = {tag["Key"]: tag["Value"] for tag in secret.get("Tags", [])}
            if tags.get(application_tag_key) != tags_by_key[application_tag_key]:
                continue
            secret_names.append(secret["Name"])

    return secret_names


def get_secret(name: str) -> dict:
    response = client.get_secret_value(SecretId=name)
    secret = {"Name": response.get("Name", name)}
    if "SecretBinary" in response:
        secret["SecretBinary"] = response["SecretBinary"]
    else:
        secret["SecretString"] = response["SecretString"]
    return secret


def batch_get(names: list[str]) -> list[dict]:
    secret_values = []
    for index in range(0, len(names), 20):
        chunk = names[index : index + 20]
        response = client.batch_get_secret_value(SecretIdList=chunk)
        secret_values.extend(response.get("SecretValues", []))
        for error in response.get("Errors", []):
            print(
                f"Failed to get {error['SecretId']}: "
                f"{error['ErrorCode']} - {error['Message']}"
            )
    return secret_values


def secret_name_to_path(base_dir: str, secret_name: str) -> str:
    """Map a dot-path secret name back to a file under base_dir."""
    parts = secret_name.split(".")
    if len(parts) == 1:
        return os.path.join(base_dir, parts[0])
    if len(parts) == 2:
        return os.path.join(base_dir, parts[0], parts[1])
    return os.path.join(base_dir, parts[0], parts[1], ".".join(parts[2:]))


def write_binary_secret(name: str, secret_value: bytes) -> None:
    path = secret_name_to_path(script_dir, name)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as secret_file:
        secret_file.write(secret_value)
    print(f"Wrote: {path}")


def process_secret_value(secret: dict) -> None:
    name = secret["Name"]
    if "SecretBinary" in secret:
        write_binary_secret(name, secret["SecretBinary"])
        return
    print(f"Retrieved: {name}")


def main() -> None:
    names = sorted(list_tagged_secret_names())
    if not names:
        return

    try:
        for secret in batch_get(names):
            process_secret_value(secret)
        # for name in names:
        #     secret = get_secret(name)
        #     process_secret_value(secret)
    except ClientError as error:
        print(f"Batch get failed: {error}")


if __name__ == "__main__":
    main()
