import paramiko
from typing import Optional, Tuple, List


import paramiko
from typing import Optional, Tuple
import os


class Ssh:
    def __init__(self, host: str, user: str, password: Optional[str] = None, port: int = 22):
     
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None

        # Define key path relative to project
        self.key_file = os.path.join(os.path.dirname(__file__), "key", "id_rsa")
        if not os.path.exists(self.key_file):
            self.key_file = None  # fallback to password if key not found

    def connect(self) -> bool:
        if self.client is not None:
            return True

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if self.key_file:
                key = paramiko.RSAKey.from_private_key_file(self.key_file, password=self.password)
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    pkey=key
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password
                )
            print(f"[V] Connected to {self.host}")
            return True
        except Exception as e:
            print(f"[X] Connection failed ssh -p {self.port} {self.user}@{self.host}")
            print(str(e))
            return False

    def run(self, command: str) -> Tuple[int, str, str]:
        if self.client is None:
            raise RuntimeError("Not connected. Call connect() first.")

        if command.strip().startswith("sudo ") and self.password:
            command = f"echo '{self.password}' | sudo -S {command[5:]}"

        stdin, stdout, stderr = self.client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8")
        err = stderr.read().decode("utf-8")
        return exit_code, out.strip(), err.strip()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            print(f"[X] Disconnected from {self.host}")



class Client:
    def __init__(self, config: dict):
        self.host = config["host"]
        self.user = config["user"]
        self.password = config["password"]
        self.role = config["role"]  # "Master" or "Worker"
        self.master_ip = config.get("master_ip")
        self.token = config.get("token")
        self.ssh = Ssh(self.host, self.user, self.password)

    def connect(self):
        self.ssh.connect()

    def update_system(self):
        print(f"[{self.host}] Connected...")

    def deploy(self, master_ip: Optional[str] = None, token: Optional[str] = None):
        if self.role == "Master" and master_ip is None:
            self.deploy_primary_master()
        elif self.role == "Master":
            self.deploy_secondary_master(master_ip, token)
        elif self.role == "Worker":
            self.deploy_worker(master_ip, token)
        else:
            print(f"[{self.host}] Unknown role: {self.role}")

    def deploy_primary_master(self):
        print(f"[{self.host}] Installing K3s Primary Master...")
        cmd = r"curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC='server --cluster-init' sh -"
        self.ssh.run(cmd)
        code, token, err = self.ssh.run("sudo cat /var/lib/rancher/k3s/server/node-token")
        self.token = token.strip()
        print(f"[{self.host}] Primary Master token: {self.token}")

    def deploy_secondary_master(self, master_ip: str, token: str):
        print(f"[{self.host}] Joining K3s cluster as Secondary Master...")
        cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"INSTALL_K3S_EXEC='server --server https://{master_ip}:6443 --token {token}' sh -"
        )
        self.ssh.run(cmd)

    def deploy_worker(self, master_ip: str, token: str):
        print(f"[{self.host}] Joining K3s cluster as Worker...")
        cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"K3S_URL=https://{master_ip}:6443 K3S_TOKEN={token} sh -"
        )
        self.ssh.run(cmd)


def deploy_cluster(cluster: List[dict]):
    # 1️⃣ Trouver le premier master automatiquement
    masters = [c for c in cluster if c["role"].lower() == "master"]
    if not masters:
        raise ValueError("No master found in configuration!")

    primary_master_config = masters[0]  # Premier master = principal
    primary = Client(primary_master_config)
    primary.connect()
    primary.update_system()
    primary.deploy()  # déploie avec --cluster-init
    master_ip = primary.host
    token = primary.token

    # 2️⃣ Déployer les autres nœuds (masters et workers)
    for node_cfg in cluster:
        if node_cfg["host"] == master_ip:
            continue  # déjà fait
        node = Client(node_cfg)
        node.connect()
        node.update_system()
        node.deploy(master_ip, token)
        node.ssh.close()

    # 3️⃣ Fermer la connexion du master principal
    primary.ssh.close()
    print("\n Cluster K3s déployé avec succès !")


if __name__ == "__main__":
    # Exemple : aucune notion de "Principal Master" à définir
    cluster_config = [
        {"host": "192.168.1.10", "user": "pi", "password": "raspberry", "role": "Master"},
        {"host": "192.168.1.11", "user": "pi", "password": "raspberry", "role": "Master"},
        {"host": "192.168.1.12", "user": "pi", "password": "raspberry", "role": "Worker"},
        {"host": "192.168.1.13", "user": "pi", "password": "raspberry", "role": "Worker"},
    ]

    deploy_cluster(cluster_config)
