import os

scriptDir = os.path.dirname(os.path.abspath(__file__))

import sys
# sys.path.insert(0, os.path.join(scriptDir, "site-packages"))

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

regionName = "ap-southeast-1"
bucketName = os.environ.get(
    "TF_STATE_BUCKET",
    "sst-s3-xxx-xxx-prd-terraform-backend-store",
)
prefix = os.environ.get("TF_STATE_PREFIX", "xxx-intranet/")
outputDir = os.path.join(scriptDir, "terraform_state", bucketName)

session = boto3.Session(region_name=regionName)
s3 = session.client("s3")


def listObjects(bucket, keyPrefix):
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=keyPrefix):
        for item in page.get("Contents") or []:
            keys.append(item)
    return keys


def safeLocalPath(key):
    parts = [part for part in key.replace("\\", "/").split("/") if part and part != ".."]
    return os.path.join(outputDir, *parts)


def main():
    print("bucket", bucketName)
    print("prefix", prefix)
    try:
        objects = listObjects(bucketName, prefix)
    except EndpointConnectionError as e:
        print("ListObjects => endpoint unreachable", e)
        return
    except ClientError as e:
        print("ListObjects =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
        return

    print("objects", len(objects))
    if not objects:
        print("empty bucket (or prefix). Check IAM s3:ListBucket / s3:GetObject.")
        return

    os.makedirs(outputDir, exist_ok=True)
    for item in objects:
        key = item["Key"]
        size = item.get("Size", 0)
        modified = item.get("LastModified")
        print(key, size, modified)
        if key.endswith("/"):
            continue
        localPath = safeLocalPath(key)
        os.makedirs(os.path.dirname(localPath), exist_ok=True)
        s3.download_file(bucketName, key, localPath)
        print("  ->", localPath)

    print("saved under", outputDir)


if __name__ == "__main__":
    main()
