"""
capture_docker_digests.py
Queries docker inspect for all running containers in the deployment
and writes deployment/docker_container_digests.json with exact RepoDigests and Image IDs.
"""
import subprocess, json
from pathlib import Path

BASE = Path(r"c:\Users\7172981\Downloads\Analytical QNLQN Model of a Microservice Application - Oct")

# Get running containers
res = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
container_names = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]

digests = {}
for name in container_names:
    cmd = ["docker", "inspect", "--format", "{{json .Image}} | {{json .Config.Image}} | {{json .RepoDigests}}", name]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out_parts = [p.strip() for p in r.stdout.strip().split(" | ")]
    img_id = out_parts[0] if len(out_parts) > 0 else ""
    cfg_img = out_parts[1] if len(out_parts) > 1 else ""
    repo_digests = out_parts[2] if len(out_parts) > 2 else ""
    try:
        repo_digests_list = json.loads(repo_digests)
    except:
        repo_digests_list = repo_digests

    digests[name] = {
        "configured_image": cfg_img.strip('"'),
        "image_id": img_id.strip('"'),
        "repo_digests": repo_digests_list
    }

out_file = BASE / "deployment/docker_container_digests.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(digests, f, indent=2)

print(f"Saved digests for {len(digests)} containers to {out_file}")
