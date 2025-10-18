import boto3

client = boto3.client("eks", region_name="us-west-2")
clusters = client.list_clusters()["clusters"]

if not clusters:
    print("No EKS clusters found in region us-west-2.")
else:
    print(f"Found {len(clusters)} clusters in us-west-2:\n")

for cluster in clusters:
    response = client.describe_cluster(name=cluster)
    cluster_info = response["cluster"]

    name = cluster_info["name"]
    status = cluster_info["status"]
    endpoint = cluster_info["endpoint"]
    version = cluster_info["version"]
    created = cluster_info["createdAt"]
    role = cluster_info["roleArn"]

    print(f"🔹 Cluster: {name}")
    print(f"   Status: {status}")
    print(f"   Version: {version}")
    print(f"   Endpoint: {endpoint}")
    print(f"   IAM Role: {role}")
    print(f"   Created At: {created}")
    print("-" * 60)
