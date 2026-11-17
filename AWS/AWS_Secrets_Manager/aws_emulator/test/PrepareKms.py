import json
import os
import ssl
import time
import urllib.request

import boto3

APPSETTINGS_PATH = os.environ.get("APPSETTINGS_PATH", "/work/appsettings.json")
REGION_NAME = os.environ.get("AWS_REGION", "ap-southeast-1")
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "")
EMULATOR_ACCOUNT = "000000000000"
CA_FILE = "/emulator/ca.pem"
HEALTH_URL = "https://127.0.0.1:9297/__admin/health"
HEALTH_ATTEMPTS = 30


def wait_until_healthy():
    context = ssl.create_default_context(cafile=CA_FILE)
    for attempt in range(HEALTH_ATTEMPTS):
        try:
            with urllib.request.urlopen(HEALTH_URL, context=context, timeout=2) as response:
                if response.status == 200:
                    print("emulator health ok")
                    return
        except Exception:
            time.sleep(1)
    raise SystemExit("emulator health check failed")


def require_emulator_account():
    if not ENDPOINT_URL:
        raise SystemExit("AWS_ENDPOINT_URL is required")
    client = boto3.client("sts", region_name=REGION_NAME, endpoint_url=ENDPOINT_URL)
    account = client.get_caller_identity()["Account"]
    if account != EMULATOR_ACCOUNT:
        raise SystemExit("refusing to continue: caller is not the emulator account")
    print("emulator account ok")


def load_kms_alias():
    with open(APPSETTINGS_PATH, encoding="utf-8") as appsettings_file:
        appsettings = json.load(appsettings_file)
    alias_name = appsettings["AwsSecretsManager"]["KmsKeyId"]
    if not alias_name.startswith("alias/"):
        raise SystemExit("KmsKeyId must be an alias")
    return alias_name


def ensure_kms_alias(alias_name):
    client = boto3.client("kms", region_name=REGION_NAME, endpoint_url=ENDPOINT_URL)
    marker = None
    while True:
        if marker:
            page = client.list_aliases(Marker=marker)
        else:
            page = client.list_aliases()
        for alias in page.get("Aliases", []):
            if alias.get("AliasName") == alias_name:
                print("KMS alias ready")
                return
        marker = page.get("NextMarker")
        if not marker:
            break
    created = client.create_key(Description="Mock emulator test key")
    client.create_alias(AliasName=alias_name, TargetKeyId=created["KeyMetadata"]["KeyId"])
    print("KMS alias created")


wait_until_healthy()
require_emulator_account()
ensure_kms_alias(load_kms_alias())
