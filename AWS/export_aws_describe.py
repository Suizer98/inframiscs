import json
import os
from datetime import date, datetime

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    OperationNotPageableError,
)

regionName = "ap-southeast-1"
scriptDir = os.path.dirname(os.path.abspath(__file__))
outputDir = os.path.join(scriptDir, "describe_json")

session = boto3.Session(region_name=regionName)
clientCache = {}

# service, operation, optional kwargs
describeCalls = [
    ("sts", "get_caller_identity", None),
    ("iam", "get_account_summary", None),
    ("iam", "list_account_aliases", None),
    ("iam", "list_instance_profiles", None),
    ("iam", "list_roles", None),
    ("ec2", "describe_account_attributes", None),
    ("ec2", "describe_availability_zones", None),
    ("ec2", "describe_vpcs", None),
    ("ec2", "describe_vpc_attribute", None),
    ("ec2", "describe_dhcp_options", None),
    ("ec2", "describe_subnets", None),
    ("ec2", "describe_route_tables", None),
    ("ec2", "describe_network_acls", None),
    ("ec2", "describe_internet_gateways", None),
    ("ec2", "describe_egress_only_internet_gateways", None),
    ("ec2", "describe_nat_gateways", None),
    ("ec2", "describe_addresses", None),
    ("ec2", "describe_network_interfaces", None),
    ("ec2", "describe_instances", None),
    ("ec2", "describe_instance_status", None),
    ("ec2", "describe_volumes", None),
    ("ec2", "describe_snapshots", {"OwnerIds": ["self"]}),
    ("ec2", "describe_images", {"Owners": ["self"]}),
    ("ec2", "describe_security_groups", None),
    ("ec2", "describe_security_group_rules", None),
    ("ec2", "describe_key_pairs", None),
    ("ec2", "describe_vpc_peering_connections", None),
    ("ec2", "describe_vpc_endpoints", None),
    ("ec2", "describe_vpc_endpoint_services", None),
    ("ec2", "describe_prefix_lists", None),
    ("ec2", "describe_managed_prefix_lists", None),
    ("ec2", "describe_flow_logs", None),
    ("ec2", "describe_transit_gateways", None),
    ("ec2", "describe_transit_gateway_attachments", None),
    ("ec2", "describe_transit_gateway_route_tables", None),
    ("ec2", "describe_vpn_gateways", None),
    ("ec2", "describe_vpn_connections", None),
    ("ec2", "describe_customer_gateways", None),
    ("ec2", "describe_tags", None),
    ("elbv2", "describe_load_balancers", None),
    ("elbv2", "describe_target_groups", None),
    ("elb", "describe_load_balancers", None),
    ("autoscaling", "describe_auto_scaling_groups", None),
    ("autoscaling", "describe_auto_scaling_instances", None),
    ("rds", "describe_db_instances", None),
    ("rds", "describe_db_clusters", None),
    ("rds", "describe_db_subnet_groups", None),
    ("elasticache", "describe_cache_clusters", None),
    ("efs", "describe_file_systems", None),
    ("fsx", "describe_file_systems", None),
    ("s3", "list_buckets", None),
    ("acm", "list_certificates", None),
    ("ssm", "describe_instance_information", None),
    ("ssm", "describe_parameters", None),
    ("secretsmanager", "list_secrets", None),
    ("kms", "list_aliases", None),
    ("ds", "describe_directories", None),
    ("lambda", "list_functions", None),
    ("cloudwatch", "describe_alarms", None),
    ("logs", "describe_log_groups", None),
    ("cloudtrail", "describe_trails", None),
    ("route53", "list_hosted_zones", None),
    ("ecs", "list_clusters", None),
    ("eks", "list_clusters", None),
    ("dynamodb", "list_tables", None),
    ("sns", "list_topics", None),
    ("sqs", "list_queues", None),
    ("events", "list_rules", None),
    ("wafv2", "list_web_acls", {"Scope": "REGIONAL"}),
]


def jsonDefault(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def stripMetadata(page):
    return {key: value for key, value in page.items() if key != "ResponseMetadata"}


def mergePages(pages):
    merged = {}
    for page in pages:
        for key, value in stripMetadata(page).items():
            if isinstance(value, list):
                merged.setdefault(key, []).extend(value)
            else:
                merged[key] = value
    return merged


def getClient(serviceName):
    if serviceName not in clientCache:
        clientCache[serviceName] = session.client(serviceName)
    return clientCache[serviceName]


def runOperation(serviceName, operation, kwargs):
    client = getClient(serviceName)
    args = kwargs or {}
    try:
        paginator = client.get_paginator(operation)
        return mergePages(paginator.paginate(**args))
    except OperationNotPageableError:
        method = getattr(client, operation)
        return stripMetadata(method(**args))


def writeJson(serviceName, fileName, payload):
    serviceDir = os.path.join(outputDir, serviceName)
    os.makedirs(serviceDir, exist_ok=True)
    path = os.path.join(serviceDir, fileName)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=jsonDefault)
    print("Wrote", path)


def collectVpcAttributes(vpcsPayload):
    client = getClient("ec2")
    rows = []
    for vpc in vpcsPayload.get("Vpcs", []):
        vpcId = vpc.get("VpcId")
        if not vpcId:
            continue
        row = {"VpcId": vpcId}
        for attribute in ("enableDnsSupport", "enableDnsHostnames"):
            try:
                out = client.describe_vpc_attribute(VpcId=vpcId, Attribute=attribute)
                row.update(stripMetadata(out))
            except ClientError as e:
                row[attribute] = e.response["Error"]["Code"]
        rows.append(row)
    return {"VpcAttributes": rows}


def collectElbv2Listeners(loadBalancersPayload):
    client = getClient("elbv2")
    listeners = []
    for loadBalancer in loadBalancersPayload.get("LoadBalancers", []):
        arn = loadBalancer.get("LoadBalancerArn")
        if not arn:
            continue
        try:
            paginator = client.get_paginator("describe_listeners")
            pageData = mergePages(paginator.paginate(LoadBalancerArn=arn))
            listeners.extend(pageData.get("Listeners", []))
        except ClientError as e:
            listeners.append(
                {
                    "LoadBalancerArn": arn,
                    "Error": e.response["Error"]["Code"],
                    "Message": e.response["Error"]["Message"],
                }
            )
    return {"Listeners": listeners}


def collectElbv2TargetHealth(targetGroupsPayload):
    client = getClient("elbv2")
    rows = []
    for group in targetGroupsPayload.get("TargetGroups", []):
        arn = group.get("TargetGroupArn")
        if not arn:
            continue
        try:
            out = client.describe_target_health(TargetGroupArn=arn)
            rows.append(
                {
                    "TargetGroupArn": arn,
                    "TargetGroupName": group.get("TargetGroupName"),
                    "TargetHealthDescriptions": out.get("TargetHealthDescriptions", []),
                }
            )
        except ClientError as e:
            rows.append(
                {
                    "TargetGroupArn": arn,
                    "Error": e.response["Error"]["Code"],
                    "Message": e.response["Error"]["Message"],
                }
            )
    return {"TargetHealth": rows}


skipStandalone = {
    ("ec2", "describe_vpc_attribute"),
}


os.makedirs(outputDir, exist_ok=True)
print("Output folder", outputDir)

results = {}
for serviceName, operation, kwargs in describeCalls:
    if (serviceName, operation) in skipStandalone:
        continue
    try:
        payload = runOperation(serviceName, operation, kwargs)
        results[(serviceName, operation)] = payload
        writeJson(serviceName, operation + ".json", payload)
    except AttributeError:
        print(serviceName, operation, "=> not available on this boto3/botocore")
    except (ClientError, BotoCoreError, ConnectTimeoutError, EndpointConnectionError) as e:
        if isinstance(e, ClientError):
            print(
                serviceName,
                operation,
                "=>",
                e.response["Error"]["Code"],
                e.response["Error"]["Message"],
            )
        else:
            print(serviceName, operation, "=>", type(e).__name__, e)

vpcsPayload = results.get(("ec2", "describe_vpcs"))
if vpcsPayload:
    try:
        writeJson("ec2", "describe_vpc_attribute.json", collectVpcAttributes(vpcsPayload))
    except (ClientError, BotoCoreError) as e:
        print("ec2 describe_vpc_attribute =>", e)

loadBalancersPayload = results.get(("elbv2", "describe_load_balancers"))
if loadBalancersPayload:
    try:
        writeJson("elbv2", "describe_listeners.json", collectElbv2Listeners(loadBalancersPayload))
    except (ClientError, BotoCoreError) as e:
        print("elbv2 describe_listeners =>", e)

targetGroupsPayload = results.get(("elbv2", "describe_target_groups"))
if targetGroupsPayload:
    try:
        writeJson(
            "elbv2",
            "describe_target_health.json",
            collectElbv2TargetHealth(targetGroupsPayload),
        )
    except (ClientError, BotoCoreError) as e:
        print("elbv2 describe_target_health =>", e)
