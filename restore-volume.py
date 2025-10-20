import boto3
from operator import itemgetter

ec2_client = boto3.client("ec2", region_name="ap-south-1")
ec2_resource = boto3.resource("ec2", region_name="ap-south-1")

instance_id = "i-02b9527e4c48a7b1c"


volumes = ec2_client.describe_volumes(
    Filters=[
        {
            "Name": "attachment.instance-id",
            "Values": [instance_id],
        }
    ]
)


isinstance_volume = volumes["Volumes"][0]


snapshots = ec2_client.describe_snapshots(
    Filters=[
        {
            "Name": "volume-id",
            "Values": [isinstance_volume["VolumeId"]],
        }
    ]
)

# Sort snapshots by date (newest first) and keep the latest
latest_snapshots = sorted(
    snapshots["Snapshots"], key=itemgetter("StartTime"), reverse=True
)[0]


new_volume = ec2_client.create_volume(
    SnapshotId=latest_snapshots["SnapshotId"],
    AvailabilityZone="ap-south-1a",
    TagSpecifications=[
        {
            "ResourceType": "volume",
            "Tags": [{"Key": "Name", "Value": "prod"}],
        }
    ],
)


while True:
    volume = ec2_resource.Volume(new_volume["VolumeId"])
    volume.load()
    if volume.state == "available":
        print(f"Volume {new_volume['VolumeId']} is now available.")
        ec2_resource.Instance(instance_id).attach_volume(
            VolumeId=new_volume["VolumeId"], Device="/dev/xvdb"
        )
        break
