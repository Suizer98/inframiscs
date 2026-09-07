# AWS (Amazon Web Services) notes

Intranet Windows EC2: boto3 loads role keys from IMDS, then calls STS / IAM over the network.

```text
1. IMDS  169.254.169.254              local instance-role keys
2. STS   sts.ap-southeast-1.amazonaws.com   who am I?
3. IAM   iam.amazonaws.com                  list policies (often blocked)
```

Scripts: `check_identity.py` (STS), `check_all_EC2_policies.py` (IAM attached + inline).

## IMDS (Instance Metadata Service)

HTTP metadata on EC2 only (not ICMP). Same address on Windows and Linux.

```powershell
$token = Invoke-RestMethod -Method PUT -Uri http://169.254.169.254/latest/api/token -Headers @{"X-aws-ec2-metadata-token-ttl-seconds"="21600"}
Invoke-RestMethod -Uri http://169.254.169.254/latest/meta-data/instance-id -Headers @{"X-aws-ec2-metadata-token"=$token}
```

```text
i-0a1b2c3d4e5f67890
```

## STS (Security Token Service)

Regional. `GetCallerIdentity` returns Account / Arn / UserId. Needs SigV4 (use AWS CLI or boto3, not a raw GET).

```powershell
Test-NetConnection sts.ap-southeast-1.amazonaws.com -Port 443
```

```text
ComputerName     : sts.ap-southeast-1.amazonaws.com
RemoteAddress    : 100.84.XX.XXX
RemotePort       : 443
InterfaceAlias   : Ethernet
SourceAddress    : 10.60.XXX.XXX
TcpTestSucceeded : True
```

`RemoteAddress` in `100.84.x.x` means a VPC endpoint / PrivateLink, not public STS.

```powershell
aws sts get-caller-identity --region ap-southeast-1
```

```text
{
    "UserId": "AROAXXXXXXXXEXAMPLE:i-0a1b2c3d4e5f67890",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/u-XXX-XXXX-iamr-ec2-profile/i-0a1b2c3d4e5f67890"
}
```

Same payload from `python check_identity.py`.

## IAM (Identity and Access Management)

Global API. Attached (managed) = reusable policy object with ARN. Inline = glued to one role, no ARN, dies with the role.

```powershell
Test-NetConnection iam.amazonaws.com -Port 443
```

If this fails while STS works, policy listing from the box will fail even though identity works.
