import boto3
from botocore.exceptions import ClientError

sm = boto3.client("secretsmanager", region_name="ap-southeast-1")

# ListSecrets => AccessDeniedException
# User: arn:aws:sts::2646221XXXXX:assumed-role/u-xxx-xxxx-iamr-ec2-profile/i-012068beaXXXXXXXX 
# is not authorized to perform: secretsmanager:ListSecrets 
# because no identity-based policy allows the secretsmanager:ListSecrets action
try:
    out = sm.list_secrets(MaxResults=5)
    print("ListSecrets => ALLOWED,", len(out.get("SecretList", [])), "secret(s)")
except ClientError as e:
    print("ListSecrets =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
