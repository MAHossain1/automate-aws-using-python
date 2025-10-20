import boto3
import schedule
from operator import itemgetter
import logging
import time
import sys
from botocore.exceptions import ClientError, BotoCoreError


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ec2_client = boto3.client("ec2", region_name="ap-south-1")


def get_prod_volumes():
    try:
        resp = ec2_client.describe_volumes(
            Filters=[{"Name": "tag:Name", "Values": ["prod"]}]
        )
        return resp.get("Volumes", [])
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to describe volumes: %s", e)
        return []


volumes = get_prod_volumes()
if not volumes:
    logger.info("No volumes found with tag 'prod'")


def cleanup_snapshots():
    volumes_local = get_prod_volumes()
    if not volumes_local:
        logger.info("No volumes to process at this run.")
        return

    for volume in volumes_local:
        volume_id = volume.get("VolumeId")
        if not volume_id:
            logger.warning("Skipping volume with missing VolumeId: %s", volume)
            continue

        try:
            snapshots_resp = ec2_client.describe_snapshots(
                OwnerIds=["self"],
                Filters=[{"Name": "volume-id", "Values": [volume_id]}],
            )
        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to describe snapshots for volume %s: %s", volume_id, e)
            continue

        snapshots = snapshots_resp.get("Snapshots", [])
        snapshot_count = len(snapshots)
        if snapshot_count == 0:
            logger.info("No snapshots found for volume %s", volume_id)
            continue
        elif snapshot_count == 1:
            logger.info("Found 1 snapshot for volume %s", volume_id)
            continue
        else:
            logger.info("Found %d snapshots for volume %s", snapshot_count, volume_id)

        # Sort snapshots by date (newest first) and keep the latest
        try:
            sorted_by_date = sorted(
                snapshots, key=itemgetter("StartTime"), reverse=True
            )
        except Exception as e:
            logger.error("Failed to sort snapshots for volume %s: %s", volume_id, e)
            continue

        # Delete all but the latest snapshot with retries
        for snap in sorted_by_date[1:]:
            snapshot_id = snap.get("SnapshotId")
            if not snapshot_id:
                logger.warning("Skipping snapshot with missing SnapshotId: %s", snap)
                continue

            attempts = 0
            max_attempts = 3
            while attempts < max_attempts:
                try:
                    ec2_client.delete_snapshot(SnapshotId=snapshot_id)
                    logger.info(
                        "Deleted snapshot %s for volume %s", snapshot_id, volume_id
                    )
                    break
                except ClientError as e:
                    attempts += 1
                    logger.warning(
                        "Attempt %d/%d: failed to delete snapshot %s for volume %s: %s",
                        attempts,
                        max_attempts,
                        snapshot_id,
                        volume_id,
                        e,
                    )
                    # exponential backoff small sleep
                    time.sleep(2**attempts)
                except BotoCoreError as e:
                    attempts += 1
                    logger.warning(
                        "Attempt %d/%d: transient error deleting snapshot %s: %s",
                        attempts,
                        max_attempts,
                        snapshot_id,
                        e,
                    )
                    time.sleep(2**attempts)
            else:
                logger.error(
                    "Giving up deleting snapshot %s after %d attempts",
                    snapshot_id,
                    attempts,
                )


# Schedule cleanup every 15 seconds
schedule.every(15).seconds.do(cleanup_snapshots)

# Main loop to run scheduled tasks
try:
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.exception("Unhandled exception while running scheduled jobs: %s", e)
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Cleanup scheduler interrupted by user, exiting.")
    sys.exit(0)
