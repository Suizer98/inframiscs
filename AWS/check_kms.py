import boto3
from botocore.exceptions import ClientError

region_name = "ap-southeast-1"
kms_key_id = "00000000-0000-0000-0000-000000000000"
key_fields = ("KeyId", "KeyState", "KeyUsage", "KeySpec", "KeyManager", "Origin")

session = boto3.Session(region_name=region_name)

try:
    key = session.client("kms").describe_key(KeyId=kms_key_id)["KeyMetadata"]
    print({field: key[field] for field in key_fields})
except ClientError as error:
    print(f"DescribeKey failed: {error.response['Error']['Code']} {error.response['Error']['Message']}")
