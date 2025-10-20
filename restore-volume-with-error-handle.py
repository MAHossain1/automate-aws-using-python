import logging
import sys
import time

import boto3
from botocore.exceptions import ClientError
from operator import itemgetter


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

ec2_client = boto3.client("ec2", region_name="ap-south-1")
ec2_resource = boto3.resource("ec2", region_name="ap-south-1")

instance_id = "i-02b9527e4c48a7b1c"


def main():
    try:
        volumes_resp = ec2_client.describe_volumes(
            Filters=[{"Name": "attachment.instance-id", "Values": [instance_id]}]
        )
    except ClientError as e:
        logging.error("Failed to describe volumes: %s", e)
        sys.exit(1)

    volumes = volumes_resp.get("Volumes", [])
    if not volumes:
        logging.error("No volumes attached to instance %s in ap-south-1.", instance_id)
        sys.exit(1)

    # pick first attached volume (you may change selection logic if needed)
    try:
        source_volume_id = volumes[0]["VolumeId"]
    except (KeyError, IndexError) as e:
        logging.error("Unexpected volume response structure: %s", e)
        sys.exit(1)

    try:
        snapshots_resp = ec2_client.describe_snapshots(
            Filters=[{"Name": "volume-id", "Values": [source_volume_id]}]
        )
    except ClientError as e:
        logging.error(
            "Failed to describe snapshots for volume %s: %s", source_volume_id, e
        )
        sys.exit(1)

    snapshots = snapshots_resp.get("Snapshots", [])
    if not snapshots:
        logging.error("No snapshots found for volume %s.", source_volume_id)
        sys.exit(1)

    # find the latest snapshot by StartTime
    try:
        latest_snapshot = max(snapshots, key=itemgetter("StartTime"))
        snapshot_id = latest_snapshot["SnapshotId"]
    except Exception as e:
        logging.error("Failed to determine latest snapshot: %s", e)
        sys.exit(1)

    logging.info("Using snapshot %s to create a new volume.", snapshot_id)

    try:
        create_resp = ec2_client.create_volume(
            SnapshotId=snapshot_id,
            AvailabilityZone="ap-south-1a",
            TagSpecifications=[
                {"ResourceType": "volume", "Tags": [{"Key": "Name", "Value": "prod"}]}
            ],
        )
    except ClientError as e:
        logging.error("Failed to create volume from snapshot %s: %s", snapshot_id, e)
        sys.exit(1)

    new_volume_id = create_resp.get("VolumeId")
    if not new_volume_id:
        logging.error("Create volume response missing VolumeId: %s", create_resp)
        sys.exit(1)

    logging.info(
        "Created volume %s, waiting for it to become available...", new_volume_id
    )

    volume = ec2_resource.Volume(new_volume_id)

    # Wait for volume to become available with timeout
    wait_timeout = 300  # seconds
    start = time.time()
    while True:
        try:
            volume.load()
        except ClientError as e:
            logging.warning("Error loading volume state (will retry): %s", e)

        state = getattr(volume, "state", None)
        if state == "available":
            logging.info("Volume %s is now available.", new_volume_id)
            break

        if time.time() - start > wait_timeout:
            logging.error(
                "Timed out waiting for volume %s to become available.", new_volume_id
            )
            sys.exit(1)

        time.sleep(5)

    # Attach volume
    try:
        ec2_resource.Instance(instance_id).attach_volume(
            VolumeId=new_volume_id, Device="/dev/xvdc"
        )
        logging.info(
            "Attach initiated for volume %s to instance %s.", new_volume_id, instance_id
        )
    except ClientError as e:
        logging.error(
            "Failed to attach volume %s to instance %s: %s",
            new_volume_id,
            instance_id,
            e,
        )
        sys.exit(1)

    # Optional: verify attachment
    attach_timeout = 120
    start = time.time()
    while True:
        try:
            volume.load()
            attachments = getattr(volume, "attachments", [])
            attached = any(
                a.get("InstanceId") == instance_id
                and a.get("State") in ("attached", "attaching")
                for a in attachments
            )
            if attached:
                logging.info(
                    "Volume %s successfully attached to %s.", new_volume_id, instance_id
                )
                break
        except ClientError:
            pass

        if time.time() - start > attach_timeout:
            logging.error(
                "Timed out waiting for volume %s to attach to instance %s.",
                new_volume_id,
                instance_id,
            )
            sys.exit(1)

        time.sleep(3)


if __name__ == "__main__":
    main()
