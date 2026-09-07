import ipaddress
import os
from collections import defaultdict

import boto3
from botocore.exceptions import ClientError, ConnectTimeoutError, EndpointConnectionError

session = boto3.Session(region_name="ap-southeast-1")
ec2 = session.client("ec2")
outputPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aws_network_diagram.md")
internalCidrMaxAddresses = 256


def tagName(resource):
    tags = {tag["Key"]: tag["Value"] for tag in resource.get("Tags", [])}
    return tags.get("Name", "")


def safeId(text):
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    cleaned = cleaned.strip("_") or "node"
    if cleaned[0].isdigit():
        cleaned = "n" + cleaned
    return cleaned


def uniqueId(base, used):
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def commonTokenPrefix(names, separator="-"):
    unique = sorted({name for name in names if name})
    splits = [name.split(separator) for name in unique]
    if len(splits) < 2:
        return []
    shortest = min(len(parts) for parts in splits)
    prefix = []
    for position in range(shortest - 1):
        tokens = {parts[position] for parts in splits}
        if len(tokens) != 1:
            break
        prefix.append(splits[0][position])
    return prefix


def shortenNames(names, separator="-"):
    prefix = commonTokenPrefix(names, separator)
    shortened = {}
    for name in names:
        parts = name.split(separator)
        if prefix and parts[: len(prefix)] == prefix:
            shortened[name] = separator.join(parts[len(prefix):])
        else:
            shortened[name] = name
    return shortened


def buildSubnetTitles(subnets, subnetIds):
    names = {}
    for subnetId in subnetIds:
        subnet = subnets.get(subnetId, {})
        names[subnetId] = tagName(subnet) or subnetId
    shortened = shortenNames(list(names.values()))
    titles = {}
    for subnetId, name in names.items():
        cidr = subnets.get(subnetId, {}).get("CidrBlock", "")
        short = shortened.get(name, name)
        titles[subnetId] = f"{short} · {cidr}" if cidr else short
    return titles


def buildNodeIds(instances, subnets, vpcs, externals, subnetTitles):
    used = set()
    vpcIds = {}
    subnetIds = {}
    subnetGroupIds = {}
    instanceIds = {}
    externalIds = {}
    for vpcId, vpc in vpcs.items():
        vpcIds[vpcId] = uniqueId(safeId(tagName(vpc) or vpcId), used)
    for subnetId, title in subnetTitles.items():
        base = safeId(title.split(" · ")[0])
        subnetIds[subnetId] = uniqueId(base, used)
        subnetGroupIds[subnetId] = uniqueId("group_" + base, used)
    for inst in instances:
        instanceIds[inst["InstanceId"]] = uniqueId(safeId(tagName(inst) or inst["InstanceId"]), used)
    for cidr in externals:
        externalIds[cidr] = uniqueId(safeId("ext_" + cidr), used)
    for inst in instances:
        vpcId = inst.get("VpcId") or "unknown"
        if vpcId not in vpcIds:
            vpcIds[vpcId] = uniqueId(safeId(vpcId), used)
    return {
        "vpc": vpcIds,
        "subnet": subnetIds,
        "subnetGroup": subnetGroupIds,
        "instance": instanceIds,
        "external": externalIds,
    }


def mermaidLabel(parts):
    return "<br/>".join(str(part) for part in parts if part).replace('"', "'")


def portLabel(rule):
    protocol = rule.get("IpProtocol", "-1")
    if protocol == "-1":
        return "all"
    fromPort = rule.get("FromPort")
    toPort = rule.get("ToPort")
    if fromPort is None:
        return protocol
    if fromPort == toPort:
        return f"{protocol}/{fromPort}"
    return f"{protocol}/{fromPort}-{toPort}"


def listInstances():
    out = ec2.describe_instances()
    rows = []
    for reservation in out.get("Reservations", []):
        rows.extend(reservation.get("Instances", []))
    return rows


def listSubnets(subnetIds):
    if not subnetIds:
        return {}
    try:
        out = ec2.describe_subnets(SubnetIds=list(subnetIds))
    except ClientError as e:
        print("DescribeSubnets =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
        return {}
    return {subnet["SubnetId"]: subnet for subnet in out.get("Subnets", [])}


def listVpcs(vpcIds):
    if not vpcIds:
        return {}
    try:
        out = ec2.describe_vpcs(VpcIds=list(vpcIds))
    except ClientError as e:
        print("DescribeVpcs =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
        return {}
    return {vpc["VpcId"]: vpc for vpc in out.get("Vpcs", [])}


def listSecurityGroups(groupIds):
    if not groupIds:
        return {}
    try:
        out = ec2.describe_security_groups(GroupIds=list(groupIds))
    except ClientError as e:
        print("DescribeSecurityGroups =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
        return {}
    return {group["GroupId"]: group for group in out.get("SecurityGroups", [])}


def instancesInCidr(cidr, instances):
    try:
        network = ipaddress.ip_network(cidr)
    except ValueError:
        return []
    if network.num_addresses > internalCidrMaxAddresses:
        return []
    matched = []
    for inst in instances:
        address = inst.get("PrivateIpAddress")
        if address and ipaddress.ip_address(address) in network:
            matched.append(inst)
    return matched


def buildEdges(instances, groups):
    instancesByGroup = defaultdict(list)
    for inst in instances:
        for group in inst.get("SecurityGroups", []):
            instancesByGroup[group["GroupId"]].append(inst)

    edges = defaultdict(set)
    externals = {}
    for inst in instances:
        target = inst["InstanceId"]
        for attached in inst.get("SecurityGroups", []):
            group = groups.get(attached["GroupId"])
            if not group:
                continue
            for rule in group.get("IpPermissions", []):
                label = portLabel(rule)
                for pair in rule.get("UserIdGroupPairs", []):
                    for source in instancesByGroup.get(pair.get("GroupId"), []):
                        if source["InstanceId"] != target:
                            edges[(source["InstanceId"], target)].add(label)
                for ipRange in rule.get("IpRanges", []):
                    cidr = ipRange.get("CidrIp")
                    if not cidr:
                        continue
                    matched = instancesInCidr(cidr, instances)
                    if matched:
                        for source in matched:
                            if source["InstanceId"] != target:
                                edges[(source["InstanceId"], target)].add(label)
                    else:
                        externals[cidr] = cidr
                        edges[(cidr, target)].add(label)
    return edges, externals


def buildLayoutMermaid(instances, subnets, vpcs, nodeIds, subnetTitles):
    lines = ["flowchart TB"]
    byVpc = {}
    for inst in instances:
        byVpc.setdefault(inst.get("VpcId") or "unknown", []).append(inst)

    for vpcId, vpcInsts in sorted(byVpc.items()):
        vpc = vpcs.get(vpcId, {})
        vpcNode = nodeIds["vpc"][vpcId]
        lines.append(
            f'  subgraph {vpcNode}["{mermaidLabel([tagName(vpc) or "VPC", vpc.get("CidrBlock", "")])}"]'
        )
        bySubnet = {}
        for inst in vpcInsts:
            bySubnet.setdefault(inst.get("SubnetId") or "unknown", []).append(inst)
        for subnetId, subnetInsts in sorted(bySubnet.items()):
            subnetNode = nodeIds["subnetGroup"][subnetId]
            title = subnetTitles.get(subnetId, subnetId)
            lines.append(f'    subgraph {subnetNode}["{title}"]')
            for inst in sorted(subnetInsts, key=lambda row: tagName(row) or row["InstanceId"]):
                instNode = nodeIds["instance"][inst["InstanceId"]]
                lines.append(
                    f'      {instNode}["{mermaidLabel([tagName(inst) or inst["InstanceId"], inst.get("PrivateIpAddress", "")])}"]'
                )
            lines.append("    end")
        lines.append("  end")
    return "\n".join(lines)


def buildSubnetAccessMermaid(instances, subnets, edges, externals, nodeIds, subnetTitles):
    instanceById = {inst["InstanceId"]: inst for inst in instances}
    subnetEdges = defaultdict(set)
    for (source, target), labels in edges.items():
        targetInst = instanceById.get(target)
        if not targetInst:
            continue
        targetSubnet = targetInst.get("SubnetId") or "unknown"
        if source in instanceById:
            sourceSubnet = instanceById[source].get("SubnetId") or "unknown"
            if sourceSubnet == targetSubnet:
                continue
            subnetEdges[(sourceSubnet, targetSubnet)].update(labels)
        else:
            subnetEdges[(source, targetSubnet)].update(labels)

    lines = ["flowchart LR"]
    for subnetId in sorted(subnetTitles):
        lines.append(f'  {nodeIds["subnet"][subnetId]}["{subnetTitles[subnetId]}"]')
    for cidr in sorted(externals):
        lines.append(f'  {nodeIds["external"][cidr]}("{cidr}")')
    for (source, target), labels in sorted(subnetEdges.items()):
        sourceNode = nodeIds["external"][source] if source in externals else nodeIds["subnet"][source]
        ports = ", ".join(sorted(labels))
        lines.append(f'  {sourceNode} -- "{ports}" --> {nodeIds["subnet"][target]}')
    return "\n".join(lines)


def buildHostAccessMermaid(instances, subnets, edges, externals, nodeIds, subnetTitles):
    lines = ["flowchart LR"]
    bySubnet = defaultdict(list)
    for inst in instances:
        bySubnet[inst.get("SubnetId") or "unknown"].append(inst)

    for subnetId, subnetInstances in sorted(bySubnet.items()):
        title = subnetTitles.get(subnetId, subnetId)
        lines.append(f'  subgraph {nodeIds["subnetGroup"][subnetId]}["{title}"]')
        for inst in sorted(subnetInstances, key=lambda row: tagName(row) or row["InstanceId"]):
            label = mermaidLabel([tagName(inst) or inst["InstanceId"], inst.get("PrivateIpAddress", "")])
            lines.append(f'    {nodeIds["instance"][inst["InstanceId"]]}["{label}"]')
        lines.append("  end")

    for cidr in sorted(externals):
        lines.append(f'  {nodeIds["external"][cidr]}("{cidr}")')

    knownInstances = {inst["InstanceId"] for inst in instances}
    for (source, target), labels in sorted(edges.items()):
        sourceNode = (
            nodeIds["instance"][source] if source in knownInstances else nodeIds["external"][source]
        )
        ports = ", ".join(sorted(labels))
        lines.append(f'  {sourceNode} -- "{ports}" --> {nodeIds["instance"][target]}')
    return "\n".join(lines)


def hostTable(instances, subnets):
    rows = ["| Host | Private IP | Subnet | Security groups |", "| --- | --- | --- | --- |"]
    for inst in sorted(instances, key=lambda row: tagName(row) or row["InstanceId"]):
        subnet = subnets.get(inst.get("SubnetId"), {})
        attached = ", ".join(
            group.get("GroupName", group["GroupId"]) for group in inst.get("SecurityGroups", [])
        )
        rows.append(
            "| {} | {} | {} | {} |".format(
                tagName(inst) or inst["InstanceId"],
                inst.get("PrivateIpAddress", ""),
                tagName(subnet) or inst.get("SubnetId", ""),
                attached,
            )
        )
    return rows


def buildMarkdown(instances, subnets, vpcs, groups, edges, externals):
    usedSubnetIds = {inst.get("SubnetId") or "unknown" for inst in instances}
    usedSubnetIds.update(subnets)
    subnetTitles = buildSubnetTitles(subnets, usedSubnetIds)
    nodeIds = buildNodeIds(instances, subnets, vpcs, externals, subnetTitles)
    return "\n".join(
        [
            "# AWS network diagram",
            "",
            "Generated from EC2 in ap-southeast-1. Arrows are inbound security-group allow rules.",
            "",
            f"Instances: {len(instances)}. Subnets: {len(subnets)}. VPCs: {len(vpcs)}. "
            f"Security groups: {len(groups)}. Edges: {len(edges)}.",
            "",
            "## Layout",
            "",
            "Where hosts live: VPC, subnet, private IP.",
            "",
            "```mermaid",
            buildLayoutMermaid(instances, subnets, vpcs, nodeIds, subnetTitles),
            "```",
            "",
            "## Access between subnets",
            "",
            "Same rules rolled up per subnet. Traffic inside a subnet is not drawn.",
            "",
            "```mermaid",
            buildSubnetAccessMermaid(instances, subnets, edges, externals, nodeIds, subnetTitles),
            "```",
            "",
            "## Access between hosts",
            "",
            "Full host-to-host detail, including same-subnet traffic.",
            "",
            "```mermaid",
            buildHostAccessMermaid(instances, subnets, edges, externals, nodeIds, subnetTitles),
            "```",
            "",
            "## Hosts",
            "",
            *hostTable(instances, subnets),
            "",
        ]
    )


try:
    instances = listInstances()
    print("DescribeInstances => ALLOWED,", len(instances), "instance(s)")
    subnetIds = {inst.get("SubnetId") for inst in instances if inst.get("SubnetId")}
    vpcIds = {inst.get("VpcId") for inst in instances if inst.get("VpcId")}
    groupIds = {
        group["GroupId"] for inst in instances for group in inst.get("SecurityGroups", [])
    }
    subnets = listSubnets(subnetIds)
    vpcs = listVpcs(vpcIds)
    groups = listSecurityGroups(groupIds)
    edges, externals = buildEdges(instances, groups)
    with open(outputPath, "w", encoding="utf-8") as handle:
        handle.write(buildMarkdown(instances, subnets, vpcs, groups, edges, externals))
    print("Wrote", outputPath)
except (ConnectTimeoutError, EndpointConnectionError) as e:
    print("EC2 => endpoint unreachable", e)
except ClientError as e:
    print("DescribeInstances =>", e.response["Error"]["Code"], e.response["Error"]["Message"])
