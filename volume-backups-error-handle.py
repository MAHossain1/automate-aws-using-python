import boto3
import schedule
import time
import logging
import sys
from botocore.exceptions import ClientError, BotoCoreError


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ec2_client = boto3.client("ec2", region_name="ap-south-1")


def create_volume_snapshots():
    try:
        resp = ec2_client.describe_volumes(
            Filters=[{"Name": "tag:Name", "Values": ["prod"]}]
        )
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to describe volumes: %s", e)
        return

    volumes = resp.get("Volumes", [])
    if not volumes:
        logger.info("No volumes found with tag 'prod'")
        return

    for volume in volumes:
        volume_id = volume.get("VolumeId")
        if not volume_id:
            logger.warning("Skipping volume with missing VolumeId: %s", volume)
            continue

        logger.info(
            "VolumeId: %s, Size: %s GiB, State: %s, Type: %s",
            volume_id,
            volume.get("Size"),
            volume.get("State"),
            volume.get("VolumeType"),
        )

        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                snapshot = ec2_client.create_snapshot(
                    VolumeId=volume_id, Description=f"Automated backup of {volume_id}"
                )
                snapshot_id = snapshot.get("SnapshotId")
                if snapshot_id:
                    logger.info(
                        "Created snapshot %s for volume %s", snapshot_id, volume_id
                    )
                else:
                    logger.warning(
                        "Create snapshot returned no SnapshotId: %s", snapshot
                    )
                break
            except ClientError as e:
                attempts += 1
                logger.warning(
                    "Attempt %d/%d: failed to create snapshot for %s: %s",
                    attempts,
                    max_attempts,
                    volume_id,
                    e,
                )
                time.sleep(2**attempts)
            except BotoCoreError as e:
                attempts += 1
                logger.warning(
                    "Attempt %d/%d: transient error creating snapshot for %s: %s",
                    attempts,
                    max_attempts,
                    volume_id,
                    e,
                )
                time.sleep(2**attempts)
        else:
            logger.error(
                "Giving up creating snapshot for %s after %d attempts",
                volume_id,
                attempts,
            )


# schedule.every(5).day.at("01:00").do(create_volume_snapshots)
schedule.every(5).seconds.do(create_volume_snapshots)

try:
    while True:
        try:
            schedule.run_pending()
        except Exception:
            logger.exception("Unhandled exception while running scheduled jobs")
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Scheduler interrupted, exiting.")
    sys.exit(0)
