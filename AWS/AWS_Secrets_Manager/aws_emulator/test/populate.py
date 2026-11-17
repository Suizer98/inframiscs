import json
import os
import time

import boto3
from botocore.exceptions import ClientError

APPSETTINGS_PATH = os.environ.get("APPSETTINGS_PATH", "/work/appsettings.json")
AWS_SETTINGS_SECTION = "AwsSecretsManager"
SECRET_DESCRIPTION = "Mock application"
SECRET_KEY_WORDS = ("password", "passphrase", "jwtsigningkey", "thumbprint")
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL") or None


def strip_json_comments(text: str) -> str:
    result = []
    index = 0
    in_string = False
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if char == "\\" and index + 1 < len(text):
                result.append(text[index + 1])
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
        elif char == '"':
            in_string = True
            result.append(char)
            index += 1
        elif text.startswith("//", index):
            newline = text.find("\n", index)
            index = len(text) if newline == -1 else newline
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = len(text) if end == -1 else end + 2
        else:
            result.append(char)
            index += 1
    return "".join(result)


with open(APPSETTINGS_PATH, encoding="utf-8-sig") as appsettings_file:
    appsettings = json.loads(strip_json_comments(appsettings_file.read()))

aws_settings = appsettings[AWS_SETTINGS_SECTION]
environment_tag_key = aws_settings["EnvironmentTagKey"]
application_tag_key = aws_settings["ApplicationTagKey"]
kms_key_id = aws_settings["KmsKeyId"]

client = boto3.client(
    "secretsmanager",
    region_name=aws_settings["Region"],
    endpoint_url=ENDPOINT_URL,
)

secret_tags = [
    {"Key": environment_tag_key, "Value": aws_settings["EnvironmentTagValue"]},
    {"Key": application_tag_key, "Value": aws_settings["ApplicationTagValue"]},
]

tags_by_key = {tag["Key"]: tag["Value"] for tag in secret_tags}


def list_tagged_secret_names() -> list[str]:
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
        except ClientError as error:
            print(f"Failed to delete {name}: {error}")


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


def upload_secret(name: str, secret_value: str) -> None:
    for attempt in range(6):
        try:
            client.create_secret(
                Name=name,
                Description=SECRET_DESCRIPTION,
                SecretString=secret_value,
                KmsKeyId=kms_key_id,
                Tags=secret_tags,
            )
            print(f"Created: {name}")
            return
        except client.exceptions.ResourceExistsException:
            described = client.describe_secret(SecretId=name)
            existing_tags = {tag["Key"]: tag["Value"] for tag in described.get("Tags", [])}
            existing_application = existing_tags.get(application_tag_key)
            if existing_application != tags_by_key[application_tag_key]:
                print(f"Skipped {name}: already used by Application={existing_application}")
                return
            client.put_secret_value(SecretId=name, SecretString=secret_value)
            client.update_secret(SecretId=name, Description=SECRET_DESCRIPTION, KmsKeyId=kms_key_id)
            client.tag_resource(SecretId=name, Tags=secret_tags)
            print(f"Updated: {name}")
            return
        except ClientError as error:
            if "scheduled for deletion" in str(error).lower() and attempt < 5:
                try:
                    client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
                except ClientError:
                    pass
                time.sleep(2)
                continue
            print(f"Failed {name}: {error}")
            return


def collect_connection_string_secrets(obj, path_prefix: str = "") -> dict:
    secrets = {}
    if not isinstance(obj, dict):
        return secrets

    for key, value in obj.items():
        if not path_prefix and key == AWS_SETTINGS_SECTION:
            continue
        secret_path = f"{path_prefix}.{key}" if path_prefix else key
        key_is_connection_string = "connectionstring" in key.lower()
        if isinstance(value, dict):
            if key_is_connection_string:
                for child_key, child_value in value.items():
                    if child_value is not None and str(child_value).strip() and not isinstance(child_value, (dict, list)):
                        secrets[f"{secret_path}.{child_key}"] = str(child_value)
            secrets.update(collect_connection_string_secrets(value, secret_path))
        elif value is not None and str(value).strip() and key_is_connection_string:
            secrets[secret_path] = str(value)

    return secrets


def collect_password_secrets(obj, path_prefix: str = "") -> dict:
    secrets = {}
    if not isinstance(obj, dict):
        return secrets

    for key, value in obj.items():
        if not path_prefix and key in (AWS_SETTINGS_SECTION, "ConnectionStrings"):
            continue
        secret_path = f"{path_prefix}.{key}" if path_prefix else key
        if isinstance(value, dict):
            secrets.update(collect_password_secrets(value, secret_path))
        elif value is not None and str(value).strip() and any(word in key.lower() for word in SECRET_KEY_WORDS):
            secrets[secret_path] = str(value)

    return secrets


delete_tagged_secrets()
wait_until_tagged_secrets_gone()

all_secrets = {**collect_connection_string_secrets(appsettings), **collect_password_secrets(appsettings)}
for name, value in sorted(all_secrets.items()):
    upload_secret(f"{tags_by_key[application_tag_key]}.{name}", value)

print(f"Uploaded {len(all_secrets)} secret(s)")
