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

## Use boto3 without changing the Python env

Do not `pip install` into any shared interpreter. Keep `boto3`, `botocore`, and dependencies in `site-packages` next to this README, then add that folder on `sys.path` before `import boto3`:

```python
import os
import sys

scriptDir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(scriptDir, "site-packages"))

import boto3
```

Typical dependencies should be `boto3`, `botocore`, `jmespath`, `s3transfer`, `dateutil`, `urllib3`, `six`. The env stays untouched; only these scripts see those packages.

## Enabling right clicking on AWS dashboard

To restore right clicking behaviour on AWS dashboard, do:

1. `Ctrl + Shift + I` on keyboard to open Developer Tools on Edge/Chrome.

2. Go to `Console` tab, on terminal type `allow pasting`.

3. Paste below and press enter:
```JavaScript
document.addEventListener('contextmenu', e => e.stopPropagation(), true);
```

## Windows failover cluster names vs EC2 IPs

`describe_instances` does not store the Windows/AD cluster name. It shows each VM node IP (`PrivateIpAddress`, primary) and extra IPs on the same NIC (`PrivateIpAddresses` with `Primary: false`). Those extra IPs are AWS secondary private IPs. AD/DNS `clus*` A records point at one of those extras (the cluster name IP). SQL listener names can have two A records, one extra on each node.

`(on 02)` means that cluster name extra IP is attached on VM 02's NIC, not that 02 is the current AG primary.

On a domain-joined Windows box, AD cluster computer objects (`clus*`) and their DNS A records:

```powershell
$q = [adsisearcher]"(&(objectCategory=computer)(name=clus*))"
$q.PageSize = 1000
$q.PropertiesToLoad.AddRange(@("name","dNSHostName"))
$q.FindAll() | ForEach-Object {
  $dns = [string]$_.Properties["dnshostname"][0]
  $a   = @()
  if ($dns) {
    $a = Resolve-DnsName $dns -ErrorAction SilentlyContinue |
         Where-Object Type -eq A
  }
  [pscustomobject]@{
    Name = [string]$_.Properties["name"][0]
    DNS  = $dns
    IP   = ($a.IPAddress | Select-Object -Unique) -join ", "
  }
} | Sort-Object Name | Format-Table -AutoSize
```

Match `IP` to extra addresses in `describe_instances`. Reverse DNS via AmazonProvidedDNS (`169.254.169.253`) only returns `ip-...compute.internal`, not the AD name.

This box's own cluster (Failover Clustering tools):

```powershell
Get-Cluster
Get-ClusterResource | Get-ClusterParameter |
  Where-Object Name -in @("Name", "DnsName", "Address")
```

Example from `describe_json2` (masked names and `10.30.x` IPs, same layout as the diagram):

| Cluster | DNS | Cluster name IP | Node IPs | Extra IPs (1st VM) | Extra IPs (2nd VM) | Extra IPs (3rd VM) |
| --- | --- | --- | --- | --- | --- | --- |
| CLUSXXXXENTDB | clusXXXXentdb.xxxx.example.com | 10.30.1.83 (on 02) | 10.30.1.73 (vm-XXXX-edb-01) / 10.30.1.74 (vm-XXXX-edb-02) | .81, .82 (.82 = XXXXentdb-lis) | .83, .84 (.84 = XXXXentdb-lis) | — |
| clusXXXXentfs | clusXXXXentfs.xxxx.example.com | 10.30.1.100 (on file-01) | 10.30.1.97 (vm-XXXX-file-01) / 10.30.1.98 (vm-XXXX-file-02) / 10.30.1.99 (vm-XXXX-file-03) | .100 | .101 | .102 |
| CLUSXXXXUNDB1 | clusXXXXundb1.xxxx.example.com | 10.30.1.93 (on udb-01) | 10.30.1.75 (vm-XXXX-udb-01) / 10.30.1.76 (vm-XXXX-udb-02) | .93, .94 | .95, .96 | — |
| clusXXXXundb3 | clusXXXXundb3.xxxx.example.com | 10.30.1.85 (on udb-03) | 10.30.1.77 (vm-XXXX-udb-03) / 10.30.1.78 (vm-XXXX-udb-04) | .85, .86 | .87, .88 | — |
| CLUSXXXXUNDB5 | clusXXXXundb5.xxxx.example.com | 10.30.1.89 (on udb-05) | 10.30.1.79 (vm-XXXX-udb-05) / 10.30.1.80 (vm-XXXX-udb-06) | .89, .90 | .91, .92 | — |
| clusXXXXjob | clusXXXXjob.xxxx.example.com | (none) | 10.30.1.9 (vm-XXXX-job-01) / 10.30.1.16 (vm-XXXX-job-02) | — | — | — |
 