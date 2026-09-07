import boto3

print("boto3 ok", boto3.__version__)
session = boto3.Session(region_name="ap-southeast-1")
sts = session.client("sts")
print(sts.get_caller_identity())
print("region", session.region_name)
