import boto3, json

# Calling global AWS IAM client, which may not work in intranet
iam = boto3.client("iam")
role = "u-XXX-XXXX-XXX-iamr-ec2-profile"

print("Attached managed policies:")
for p in iam.list_attached_role_policies(RoleName=role)["AttachedPolicies"]:
    print(p["PolicyName"], p["PolicyArn"])
    ver = iam.get_policy(PolicyArn=p["PolicyArn"])["Policy"]["DefaultVersionId"]
    doc = iam.get_policy_version(PolicyArn=p["PolicyArn"], VersionId=ver)["PolicyVersion"]["Document"]
    print(json.dumps(doc, indent=2))

print("Inline policies:")
for name in iam.list_role_policies(RoleName=role)["PolicyNames"]:
    doc = iam.get_role_policy(RoleName=role, PolicyName=name)["PolicyDocument"]
    print(name)
    print(json.dumps(doc, indent=2))
