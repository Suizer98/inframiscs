import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

session = boto3.Session(region_name="ap-southeast-1")
s3 = session.client("s3")

# ListBuckets => ALLOWED, 5 bucket(s)
# sst-s3-XXX-XXXX-XXX-alb-logs 2026-04-23 18:27:32+00:00
# sst-s3-XXX-XXXX-XXX-ct-logs01 2026-04-23 22:48:10+00:00
# sst-s3-XXX-XXXX-XXX-s3-access-logs 2026-04-23 22:06:48+00:00
# sst-s3-XXX-XXXX-XXX-share 2026-04-23 20:29:13+00:00
# sst-s3-XXX-XXXX-XXX-terraform-backend-store 2026-04-23 19:58:12+00:00

try:
    out = s3.list_buckets()
    buckets = out.get("Buckets", [])
    print("ListBuckets => ALLOWED,", len(buckets), "bucket(s)")
    for bucket in buckets:
        print(bucket["Name"], bucket.get("CreationDate"))
except EndpointConnectionError as e:
    print("ListBuckets => endpoint unreachable", e)
except ClientError as e:
    print("ListBuckets =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
