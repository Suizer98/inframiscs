import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

session = boto3.Session(region_name="ap-southeast-1")
logs = session.client("logs")
cw = session.client("cloudwatch")

# DescribeLogGroups => ALLOWED, 22 group(s)
# /aws/kinesisfirehose/XXX-central-logging-firehose 0
# /aws/lambda/XXX-central-logging-firehose-lambda 21732279309
# /aws/lambda/XXX-modify-sechub-severity-label-lambda 14020
# /aws/lambda/XXX-pac-iam-event-sns-to-EventBridge 648548
# /aws/lambda/XXX-pac-rules-GT1_3-subscription-to-central-gcci-logs 860439
# /aws/lambda/XXX-pac-rules-GT1_4-cloudwatch-alarms-compliance 863291
# /aws/lambda/XXX-pac-rules-GT1_5-SSM-patch-baselines-configured-compliance 732471
# /aws/lambda/XXX-pac-rules-GT1_6-minimal-tags 4583345
# /aws/lambda/XXX-pac-rules-GT1_7-igw-chgtrigger-for-vpc-taggen-or-gencidr 904758
# /aws/lambda/XXX-pac-rules-GT1_8-vpc-taggen-with-routableCIDR 2544812
# /aws/lambda/XXX-pac-rules-GT2_1-vpc-peering-with-ext 14036
# /aws/lambda/XXX-pac-rules-GT2_1-vpc-peering-with-ext-org 523262
# /aws/lambda/XXX-pac-rules-GT2_1-vpc-peering-with-ext-org-refresh 1010
# /aws/lambda/XXX-pac-rules-GT2_2-check-transit-gateway-peering 10966
# /aws/lambda/XXX-pac-rules-GT2_3-assume-role-policy-with-ext 279934
# /aws/lambda/XXX-pac-rules-GT2_4-asterisk-iam-actions 121285
# /aws/lambda/XXX-pac-rules-GT2_6-capacity-monitoring-put-ebs-size 140192
# /aws/lambda/XXX-pac-rules-GT2_6-capacity-monitoring-put-ec2-count 413111
# /aws/lambda/XXX-pac-rules-GT2_6-capacity-monitoring-suspend-asg 7631
# cwl-XXX-ec2-logs 49831071019
# cwl-XXX-ct-logs01 37441621338
# vpc-flowlog-loggroup-vpc-019b361fb703cb0f4 47453861608
# DescribeAlarms => ALLOWED, 5 alarm(s)
# cwa-XXX-XXXapp-XX-01-cpu-95 OK
# cwa-XXX-XXXapp-XX-01-disk-C-80 OK
# cwa-XXX-XXXapp-XX-01-disk-C-90 OK
# cwa-XXX-XXXapp-XX-01-disk-D-80 OK
# cwa-XXX-XXXapp-XX-01-disk-D-90 OK

try:
    out = logs.describe_log_groups(limit=5)
    groups = out.get("logGroups", [])
    print("DescribeLogGroups => ALLOWED,", len(groups), "group(s)")
    for group in groups:
        print(group.get("logGroupName"), group.get("storedBytes"))
except EndpointConnectionError as e:
    print("DescribeLogGroups => endpoint unreachable", e)
except ClientError as e:
    print("DescribeLogGroups =>", e.response["Error"]["Code"], e.response["Error"]["Message"])

try:
    out = cw.describe_alarms(MaxRecords=5)
    alarms = out.get("MetricAlarms", [])
    print("DescribeAlarms => ALLOWED,", len(alarms), "alarm(s)")
    for alarm in alarms:
        print(alarm.get("AlarmName"), alarm.get("StateValue"))
except EndpointConnectionError as e:
    print("DescribeAlarms => endpoint unreachable", e)
except ClientError as e:
    print("DescribeAlarms =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
