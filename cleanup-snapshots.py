import boto3
import schedule
from operator import itemgetter
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize EC2 client
ec2_client = boto3.client("ec2", region_name="ap-south-1")

# Get volumes tagged with 'prod'
volumes = ec2_client.describe_volumes(
    Filters=[{"Name": "tag:Name", "Values": ["prod"]}]
)

if not volumes:
    logger.info("No volumes found with tag 'prod'")


def cleanup_snapshots():
    # Process each volume
    for volume in volumes["Volumes"]:
        # Get snapshots for the volume
        snapshots = ec2_client.describe_snapshots(
            OwnerIds=["self"],
            Filters=[{"Name": "volume-id", "Values": [volume["VolumeId"]]}],
        )

        # Display messages based on snapshot count
        snapshot_count = len(snapshots)
        if snapshot_count == 0:
            logger.info(f"No snapshots found for volume")
        elif snapshot_count == 1:
            logger.info(f"Found 1 snapshot for volume")
        else:
            logger.info(f"Found {snapshot_count} snapshots for volume")

        # Sort snapshots by date (newest first) and keep the latest
        sorted_by_date = sorted(
            snapshots["Snapshots"], key=itemgetter("StartTime"), reverse=True
        )

        # Delete all but the latest snapshot
        for snap in sorted_by_date[1:]:
            response = ec2_client.delete_snapshot(SnapshotId=snap["SnapshotId"])
            print(response)


# Schedule cleanup every 5 seconds
schedule.every(15).seconds.do(cleanup_snapshots)

# Main loop to run scheduled tasks
while True:
    schedule.run_pending()
