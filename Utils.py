import paramiko
from typing import Optional, Tuple, List
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ------------------------------
# SSH Helper Class
# ------------------------------
class Ssh:
    def __init__(self, host: str, user: str, port: int = 22):
        self.host = host
        self.user = user
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None

        self.key_file = os.path.join(os.path.dirname(__file__), "key", "id_rsa")
        if not os.path.exists(self.key_file):
            raise FileNotFoundError(f"Key file not found: {self.key_file}")

    def connect(self) -> bool:
        if self.client is not None:
            return True
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            key = paramiko.RSAKey.from_private_key_file(self.key_file)
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                pkey=key,
                look_for_keys=False,
                allow_agent=False
            )
            print(f"Connected to {self.host}")
            return True
        except Exception as e:
            print(f"Connection failed ssh -p {self.port} {self.user}@{self.host}")
            print(str(e))
            return False

    def run(self, command: str, verbose: bool = False) -> Tuple[int, str, str]:
        """
        Run a command on the remote host.
        If verbose=True, streams stdout and stderr live.
        """
        if self.client is None:
            raise RuntimeError("Not connected. Call connect() first.")

        stdin, stdout, stderr = self.client.exec_command(command)
        out_lines = []
        err_lines = []

        if verbose:
            while not stdout.channel.exit_status_ready():
                while stdout.channel.recv_ready():
                    line = stdout.channel.recv(1024).decode("utf-8")
                    print(f"[{self.host}] {line}", end="")
                    out_lines.append(line)
                while stderr.channel.recv_stderr_ready():
                    line = stderr.channel.recv_stderr(1024).decode("utf-8")
                    print(f"[{self.host}][ERR] {line}", end="")
                    err_lines.append(line)
            # Capture any remaining output
            out_lines.append(stdout.read().decode("utf-8"))
            err_lines.append(stderr.read().decode("utf-8"))
        else:
            out_lines.append(stdout.read().decode("utf-8"))
            err_lines.append(stderr.read().decode("utf-8"))

        exit_code = stdout.channel.recv_exit_status()
        return exit_code, "".join(out_lines).strip(), "".join(err_lines).strip()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            print(f"Disconnected from {self.host}")

# ------------------------------
# Client (Cluster Node) Class
# ------------------------------
class Client:
    def __init__(self, config: dict):
        self.host = config["host"]
        self.user = config["user"]
        self.role = config["role"]
        self.master_ip = config.get("master_ip")
        self.token = config.get("token")
        self.ssh = Ssh(self.host, self.user)
        if not self.ssh.connect():
            raise RuntimeError(f"Connect Failed to {self.role} {self.host}")

    def deploy(self, master_ip: Optional[str] = None, token: Optional[str] = None, verbose: bool = False):
        if self.role.lower() == "master" and master_ip is None:
            self.deploy_primary_master(verbose)
        elif self.role.lower() == "master":
            self.deploy_secondary_master(master_ip, token, verbose)
        elif self.role.lower() == "worker":
            self.deploy_worker(master_ip, token, verbose)
        else:
            print(f"{self.host}: Unknown role {self.role}")

    def deploy_primary_master(self, verbose: bool = False):
        print(f"{self.host}: Installing K3s Primary Master...")
        cmd = r"curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC='server --cluster-init' sh -"
        self.ssh.run(cmd, verbose)
        _, token, _ = self.ssh.run("sudo cat /var/lib/rancher/k3s/server/node-token", verbose)
        self.token = token.strip()
        print(f"{self.host}: Primary Master token: {self.token}")

    def deploy_secondary_master(self, master_ip: str, token: str, verbose: bool = False):
        print(f"{self.host}: Joining K3s cluster as Secondary Master...")
        cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"INSTALL_K3S_EXEC='server --server https://{master_ip}:6443 --token {token}' sh -"
        )
        self.ssh.run(cmd, verbose)

    def deploy_worker(self, master_ip: str, token: str, verbose: bool = False):
        print(f"{self.host}: Joining K3s cluster as Worker...")
        cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"K3S_URL=https://{master_ip}:6443 K3S_TOKEN={token} sh -"
        )
        self.ssh.run(cmd, verbose)

# ------------------------------
# Helper for multithreaded node deployment
# ------------------------------
def deploy_node(node_cfg: dict, master_ip: str, token: str, verbose: bool = False):
    node = Client(node_cfg)
    node.deploy(master_ip, token, verbose)
    node.ssh.close()
    return node.host

# ------------------------------
# Cluster Deployment
# ------------------------------
def deploy_cluster(cluster: List[dict], verbose: bool = False) -> Client:
    # Find primary master
    masters = [c for c in cluster if c["role"].lower() == "master"]
    if not masters:
        raise ValueError("No master found in configuration!")

    primary_master_config = masters[0]
    primary = Client(primary_master_config)
    primary.deploy(verbose=verbose)
    master_ip = primary.host
    token = primary.token

    # Deploy other nodes in parallel
    other_nodes = [c for c in cluster if c["host"] != master_ip]
    if other_nodes:
        print("\nDeploying other nodes...")
        with ThreadPoolExecutor(max_workers=len(other_nodes)) as executor:
            futures = {
                executor.submit(deploy_node, cfg, master_ip, token, verbose): cfg["host"]
                for cfg in other_nodes
            }
            for future in tqdm(as_completed(futures), total=len(futures), desc="Deploying nodes"):
                host = future.result()
                print(f"{host} deployed successfully")

    print("\nK3s cluster deployed successfully! Primary master connection remains open.")
    return primary

# ------------------------------
# App Deployment (host-specific)
# ------------------------------
def deploy_apps(cluster_nodes: List[Client], app_file: str = "app.json", verbose: bool = True):
    import os

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

        if target_host == "any":
            primary_master = cluster_nodes[0]
            print(f"{app_type}: Deploying to primary master...")
            cmd = f"kubectl apply -f {yaml_path}"
            code, out, err = primary_master.ssh.run(cmd, verbose=verbose)
            if code == 0:
                print(f"{app_type} deployed successfully:\n{out}")
            else:
                print(f"{app_type} deployment failed:\n{err}")
        else:
            matched_nodes = [node for node in cluster_nodes if node.host == target_host]
            if not matched_nodes:
                print(f"{app_type}: No node found with host {target_host}, skipping.")
                continue
            node = matched_nodes[0]
            print(f"{app_type}: Deploying to {node.host}...")
            cmd = f"kubectl apply -f {yaml_path}"
            code, out, err = node.ssh.run(cmd, verbose=verbose)
            if code == 0:
                print(f"{app_type} deployed successfully on {node.host}:\n{out}")
            else:
                print(f"{app_type} deployment failed on {node.host}:\n{err}")

# ------------------------------
# Main
# ------------------------------
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

    # Example: run kubectl command interactively
    code, out, err = primary_master.ssh.run("kubectl get pods --all-namespaces", verbose=True)
    print(out)
