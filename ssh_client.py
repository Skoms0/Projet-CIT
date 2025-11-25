import paramiko
import os
from typing import Optional, Tuple

class Ssh:
    def __init__(self, host: str, user: str, port: int = 22):
        self.host = host
        self.user = user
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None

        self.key_file = os.path.expanduser("~/.ssh/id_rsa")
        if not os.path.exists(self.key_file):
            raise FileNotFoundError(f"Key file not found: {self.key_file}")

        self.proxy_command = f"ssh -l {self.user} -W {self.host}:{self.port} khamul"
        self.proxy = paramiko.ProxyCommand(self.proxy_command)

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
                sock=self.proxy,
                allow_agent=False,
                look_for_keys=False,
                timeout=10
            )

            print(f"Connected to {self.host} via khamul")
            return True

        except Exception as e:
            print(f"Connection failed ssh -p {self.port} {self.user}@{self.host}")
            print("Proxy used:", self.proxy_command)
            print(str(e))
            return False
        
    def run(self, command: str, verbose: bool = False) -> Tuple[int, str, str]:
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

    def upload(self, local_path: str, remote_path: str):
        if self.client is None:
            raise RuntimeError("Not connected. Call connect() first.")
        sftp = self.client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
