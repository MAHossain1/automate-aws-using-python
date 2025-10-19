import boto3
import schedule

ec2_client = boto3.client("ec2", region_name="ap-south-1")


def create_volume_snapshots():
    volumes = ec2_client.describe_volumes(
        Filters=[{"Name": "tag:Name", "Values": ["prod"]}]
    )
    for volume in volumes["Volumes"]:
        print(
            f"VolumeId: {volume['VolumeId']}, Size: {volume['Size']} GiB, State: {volume['State']}, Type: {volume['VolumeType']}"
        )
        new_snapshot = ec2_client.create_snapshot(VolumeId=volume["VolumeId"])
        print(
            f"\tCreated snapshot {new_snapshot['SnapshotId']} for volume {volume['VolumeId']}"
        )


# schedule.every(5).day.at("01:00").do(create_volume_snapshots)

schedule.every(5).seconds.do(create_volume_snapshots)

while True:
    schedule.run_pending()
