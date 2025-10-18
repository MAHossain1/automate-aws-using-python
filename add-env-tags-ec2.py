import boto3

# Mumbai region
ec2_client_mumbai = boto3.client("ec2", region_name="ap-south-1")
ec2_resource_mumbai = boto3.resource("ec2", region_name="ap-south-1")

# Frankfurt region
ec2_client_frankfurt = boto3.client("ec2", region_name="eu-central-1")
ec2_resource_frankfurt = boto3.resource("ec2", region_name="eu-central-1")

instances_ids_mumbai = []
instances_ids_frankfurt = []

# Get all instances from Mumbai
reservations_mumbai = ec2_client_mumbai.describe_instances()["Reservations"]
for res in reservations_mumbai:
    for instance in res["Instances"]:
        instances_ids_mumbai.append(instance["InstanceId"])

print("Mumbai Instances IDs:", instances_ids_mumbai)

# Tag Mumbai instances
if instances_ids_mumbai:
    ec2_resource_mumbai.create_tags(
        Resources=instances_ids_mumbai,
        Tags=[
            {"Key": "env", "Value": "prod"},
            {"Key": "team", "Value": "research"},
        ],
    )

# Get all instances from Frankfurt
reservations_frankfurt = ec2_client_frankfurt.describe_instances()["Reservations"]
for res in reservations_frankfurt:
    for instance in res["Instances"]:
        instances_ids_frankfurt.append(instance["InstanceId"])

print("Frankfurt Instances IDs:", instances_ids_frankfurt)

# Tag Frankfurt instances
if instances_ids_frankfurt:
    ec2_resource_frankfurt.create_tags(
        Resources=instances_ids_frankfurt,
        Tags=[
            {"Key": "env", "Value": "dev"},
            {"Key": "team", "Value": "research and development"},
        ],
    )
