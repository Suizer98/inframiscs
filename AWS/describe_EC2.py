import urllib.request

import boto3
from botocore.exceptions import ClientError, ConnectTimeoutError, EndpointConnectionError

session = boto3.Session(region_name="ap-southeast-1")
ec2 = session.client("ec2")

# ThisInstance => ALLOWED i-0...
# DescribeInstances => ALLOWED, 11 instance(s) on first page
# i-0... vm-X-app-01 running r5.xlarge 10.59.x.x vpc-0... subnet-0app... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-app-02 running r5.2xlarge 10.59.x.x vpc-0... subnet-0app... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-app-03 running r5.xlarge 10.59.x.x vpc-0... subnet-0app... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-app-04 running r5.xlarge 10.59.x.x vpc-0... subnet-0app... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-file-01 running m5.xlarge 10.59.x.x vpc-0... subnet-0db... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-file-02 running r5.2xlarge 10.59.x.x vpc-0... subnet-0db... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-db-01 running r5.xlarge 10.59.x.x vpc-0... subnet-0db... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-db-02 running r5.xlarge 10.59.x.x vpc-0... subnet-0db... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-db-03 running r5.xlarge 10.59.x.x vpc-0... subnet-0db... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-web-01 running m5.xlarge 10.59.x.x vpc-0... subnet-0web... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile
# i-0... vm-X-proxy-01 running m5.xlarge 10.59.x.x vpc-0... subnet-0proxy... arn:aws:iam::XXXXXXXXXXXX:instance-profile/u-XXX-XXXX-iamr-ec2-profile


def readInstanceId():
    tokenReq = urllib.request.Request(
        "http://169.254.169.254/latest/api/token",
        method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
    )
    token = urllib.request.urlopen(tokenReq, timeout=2).read().decode()
    idReq = urllib.request.Request(
        "http://169.254.169.254/latest/meta-data/instance-id",
        headers={"X-aws-ec2-metadata-token": token},
    )
    return urllib.request.urlopen(idReq, timeout=2).read().decode()


def printInstance(inst):
    tags = {tag["Key"]: tag["Value"] for tag in inst.get("Tags", [])}
    profile = (inst.get("IamInstanceProfile") or {}).get("Arn", "-")
    print(
        inst["InstanceId"],
        tags.get("Name", "-"),
        inst["State"]["Name"],
        inst["InstanceType"],
        inst.get("PrivateIpAddress"),
        inst.get("VpcId"),
        inst.get("SubnetId"),
        profile,
    )


try:
    instanceId = readInstanceId()
    out = ec2.describe_instances(InstanceIds=[instanceId])
    print("ThisInstance => ALLOWED", instanceId)
    for reservation in out.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            printInstance(inst)
except OSError as e:
    print("ThisInstance => IMDS failed", e)
except (ConnectTimeoutError, EndpointConnectionError) as e:
    print("ThisInstance => endpoint unreachable", e)
except ClientError as e:
    print("ThisInstance =>", e.response["Error"]["Code"], e.response["Error"]["Message"])

try:
    out = ec2.describe_instances()
    rows = [inst for reservation in out.get("Reservations", []) for inst in reservation.get("Instances", [])]
    print("DescribeInstances => ALLOWED,", len(rows), "instance(s) on first page")
    for inst in rows:
        printInstance(inst)
except (ConnectTimeoutError, EndpointConnectionError) as e:
    print("DescribeInstances => endpoint unreachable", e)
except ClientError as e:
    print("DescribeInstances =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
