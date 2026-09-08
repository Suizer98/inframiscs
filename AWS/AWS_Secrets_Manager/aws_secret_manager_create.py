import json
import os
import time

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
scheduledjobs_path = os.path.join(script_dir, "scheduledjobs.json")

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


def delete_tagged_secrets() -> None:
    for name in list_tagged_secret_names():
        try:
            client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
            print(f"Deleted: {name}")
        except ClientError as e:
            print(f"Failed to delete {name}: {e}")


def wait_until_tagged_secrets_gone(*, timeout: float = 120, interval: float = 1) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = list_tagged_secret_names()
        if not remaining:
            return
        print(f"Waiting for {len(remaining)} secret(s) to finish deleting...")
        time.sleep(interval)

    remaining = list_tagged_secret_names()
    raise TimeoutError(
        f"Tagged secrets still present after {timeout}s: {', '.join(sorted(remaining))}"
    )


def upload_secret(name: str, secret_value, *, is_binary: bool = False) -> None:
    create_kwargs = {"Name": name, "Tags": secret_tags}
    update_kwargs = {"SecretId": name}
    if is_binary:
        create_kwargs["SecretBinary"] = secret_value
        update_kwargs["SecretBinary"] = secret_value
    else:
        create_kwargs["SecretString"] = secret_value
        update_kwargs["SecretString"] = secret_value

    for attempt in range(6):
        try:
            client.create_secret(**create_kwargs)
            print(f"Created: {name}")
            return
        except client.exceptions.ResourceExistsException:
            client.put_secret_value(**update_kwargs)
            client.tag_resource(SecretId=name, Tags=secret_tags)
            print(f"Updated: {name}")
            return
        except ClientError as e:
            if "scheduled for deletion" in str(e).lower() and attempt < 5:
                try:
                    client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
                except ClientError:
                    pass
                time.sleep(2)
                continue
            print(f"Failed {name}: {e}")
            return


def blob_secret_name(base_dir: str, file_path: str) -> str:
    """Map a file under BatchJobs to a dot-path secret name, preserving dots in filenames."""
    rel_path = os.path.relpath(file_path, base_dir)
    parts = rel_path.split(os.sep)
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]}.{parts[1]}"
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def collect_password_secrets(obj, path_prefix: str = "") -> dict:
    """
    Collect string secrets for keys containing 'password' (case-insensitive).
    """
    secrets = {}
    if not isinstance(obj, dict):
        return secrets

    for key, value in obj.items():
        secret_path = f"{path_prefix}.{key}" if path_prefix else key
        if isinstance(value, dict):
            secrets.update(collect_password_secrets(value, secret_path))
        elif "password" in key.lower() and value is not None:
            secrets[secret_path] = str(value)

    return secrets


with open(scheduledjobs_path, encoding="utf-8") as scheduledjobs_file:
    scheduledjobs = json.load(scheduledjobs_file)

delete_tagged_secrets()
wait_until_tagged_secrets_gone()

for section_name, entries in scheduledjobs.items():
    if not isinstance(entries, dict):
        continue
    for filename in sorted({v for v in entries.values() if isinstance(v, str) and v.lower().endswith(".sde")}):
        path = os.path.join(script_dir, section_name, filename)
        if not os.path.isfile(path):
            print(f"Skipped {section_name}.{filename}: file not found at {path}")
            continue
        with open(path, "rb") as connection_file:
            upload_secret(blob_secret_name(script_dir, path), connection_file.read(), is_binary=True)

certificates_and_keys_dir = os.path.join(script_dir, "CertificatesAndKeys")
if os.path.isdir(certificates_and_keys_dir):
    for dirpath, _, filenames in os.walk(certificates_and_keys_dir):
        for filename in sorted(filenames):
            file_path = os.path.join(dirpath, filename)
            with open(file_path, "rb") as cert_file:
                upload_secret(blob_secret_name(script_dir, file_path), cert_file.read(), is_binary=True)

for name, value in sorted(collect_password_secrets(scheduledjobs).items()):
    upload_secret(name, value)
