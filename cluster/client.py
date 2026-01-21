from typing import Optional
from ssh_client import Ssh

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
