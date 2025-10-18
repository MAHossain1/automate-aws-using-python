import boto3

import schedule


ec2_client = boto3.client("ec2", region_name="ap-south-1")
ec2_resource = boto3.resource("ec2", region_name="ap-south-1")


reservations = ec2_client.describe_instances()

# for reservation in reservations["Reservations"]:
#     for instance in reservation["Instances"]:
#         print(f"Id: {instance['InstanceId']}, State: {instance['State']['Name']}")


def check_instance_status():
    statuses = ec2_client.describe_instance_status(
        IncludeAllInstances=True,
    )
    for status in statuses["InstanceStatuses"]:
        ins_status = status["InstanceStatus"]["Status"]
        ins_system = status["SystemStatus"]["Status"]
        state = status["InstanceState"]["Name"]
        print(
            f"Instance {status['InstanceId']} has instance status {ins_status} and system status {ins_system} and present state is {state}"
        )


schedule.every(5).seconds.do(check_instance_status)
while True:
    schedule.run_pending()

# routeTables = ec2_client.describe_route_tables()
# for routeTable in routeTables["RouteTables"]:
#     print(routeTable["RouteTableId"])
#     for association in routeTable["Associations"]:
#         print(f"\tAssociationId: {association['RouteTableAssociationId']}")
#         print(f"\tMain: {association['Main']}")
#         if "SubnetId" in association:
#             print(f"\tSubnetId: {association['SubnetId']}")
#         print("")


# azs = ec2_client.describe_availability_zones()
# for az in azs["AvailabilityZones"]:
#     # print(f"Name: {az['ZoneName']}, State: {az['State']}, Region: {az['RegionName']}")
#     print(f"{az['ZoneName']} - {az['Messages']}, region - {az['RegionName']}")


# securityGroups = ec2_client.describe_security_groups()

# for securityGroup in securityGroups["SecurityGroups"]:
# print(f"Security Group Name: {securityGroup['GroupName']}, Id: {securityGroup['GroupId']}")
# for rule in securityGroup['IpPermissions']:
#     print(f"\tIP Protocol: {rule['IpProtocol']}, From Port: {rule.get('FromPort')}, To Port: {rule.get('ToPort')}")
#     for ipRange in rule['IpRanges']:
#         print(f"\t\tCIDR: {ipRange['CidrIp']}")
# print("")
# print(
#     f"security group name: {securityGroup['GroupName']}, id: {securityGroup['GroupId']}"
# )

# for IpPermission in securityGroup["IpPermissions"]:
#     print(
#         f"\tIP Protocol: {IpPermission['IpProtocol']}, From Port: {IpPermission.get('FromPort')}, To Port: {IpPermission.get('ToPort')}"
#     )
