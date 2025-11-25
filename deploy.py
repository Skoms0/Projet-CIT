from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List
from client import Client

def deploy_node(node_cfg: dict, master_ip: str, token: str, verbose: bool = False):
    node = Client(node_cfg)
    node.deploy(master_ip, token, verbose)
    node.ssh.close()
    return node.host

def deploy_cluster(cluster: List[dict], verbose: bool = False) -> Client:
    masters = [c for c in cluster if c["role"].lower() == "master"]
    if not masters:
        raise ValueError("No master found in configuration!")

    primary_master_config = masters[0]
    primary = Client(primary_master_config)
    primary.deploy(verbose=verbose)
    master_ip = primary.host
    token = primary.token

    other_nodes = [c for c in cluster if c["host"] != master_ip]
    if other_nodes:
        print("\nDeploying other nodes...")
        with ThreadPoolExecutor(max_workers=len(other_nodes)) as executor:
            futures = {executor.submit(deploy_node, cfg, master_ip, token, verbose): cfg["host"] for cfg in other_nodes}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Deploying nodes"):
                host = future.result()
                print(f"{host} deployed successfully")

    print("\nK3s cluster deployed successfully! Primary master connection remains open.")
    return primary
