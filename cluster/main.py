import json
from client import Client
from deploy import deploy_cluster, deploy_node
from app import deploy_apps

if __name__ == "__main__":
    with open("cluster_config.json", "r") as file:
        cluster_config = json.load(file)

    # Deploy cluster
    primary_master = deploy_cluster(cluster_config, verbose=True)

    # Build list of all nodes (primary + others)
    cluster_nodes = [primary_master]
    for node_cfg in cluster_config:
        if node_cfg["host"] != primary_master.host:
            cluster_nodes.append(Client(node_cfg))

    # Deploy apps from app.json
    deploy_apps(cluster_nodes, app_file="app.json", verbose=True)

    # Optional interactive command
    code, out, err = primary_master.ssh.run("sudo kubectl get pods --all-namespaces", verbose=True)
    print(out)
