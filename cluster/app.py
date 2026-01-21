import json
import os
from client import Client

def deploy_apps(cluster_nodes: list, app_file: str = "app.json", verbose: bool = True):

    if not os.path.exists(app_file):
        print(f"App file {app_file} not found.")
        return

    with open(app_file, "r") as f:
        apps = json.load(f)

    for app in apps:
        app_type = app.get("type")
        yaml_file = app.get("fichier")
        target_host = app.get("host", "any")

        yaml_path = os.path.join("config", yaml_file)
        if not os.path.exists(yaml_path):
            print(f"{app_type}: YAML file {yaml_path} not found, skipping.")
            continue

        remote_path = f"/tmp/{yaml_file}"

        if target_host == "any":
            primary_master = cluster_nodes[0]
            print(f"{app_type}: Uploading {yaml_file} to primary master...")
            primary_master.ssh.upload(yaml_path, remote_path)
            cmd = f"sudo kubectl apply -f {remote_path}"
            code, out, err = primary_master.ssh.run(cmd, verbose=verbose)

        else:
            matched = [n for n in cluster_nodes if n.host == target_host]
            if not matched:
                print(f"{app_type}: No node found with host {target_host}, skipping.")
                continue

            node = matched[0]
            print(f"{app_type}: Uploading {yaml_file} to {node.host}...")
            node.ssh.upload(yaml_path, remote_path)
            cmd = f"sudo kubectl apply -f {remote_path}"
            code, out, err = node.ssh.run(cmd, verbose=verbose)

        if code == 0:
            print(f"{app_type} deployed successfully:\n{out}")
        else:
            print(f"{app_type} deployment failed:\n{err}")
