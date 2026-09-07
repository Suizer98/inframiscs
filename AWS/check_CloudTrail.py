import boto3
from botocore.exceptions import ClientError, ConnectTimeoutError, EndpointConnectionError

session = boto3.Session(region_name="ap-southeast-1")
ct = session.client("cloudtrail")

# DescribeTrails => endpoint unreachable
# Connect timeout on endpoint URL: "https://cloudtrail.ap-southeast-1.amazonaws.com/"

try:
    out = ct.describe_trails()
    trails = out.get("trailList", [])
    print("DescribeTrails => ALLOWED,", len(trails), "trail(s)")
    for trail in trails:
        print(trail.get("Name"), trail.get("S3BucketName"), trail.get("IsMultiRegionTrail"))
except (ConnectTimeoutError, EndpointConnectionError) as e:
    print("DescribeTrails => endpoint unreachable", e)
except ClientError as e:
    print("DescribeTrails =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
