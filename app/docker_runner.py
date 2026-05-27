import subprocess
import uuid
import os
from pathlib import Path

class DockerRunner:
    def __init__(self, workspace: str = "/tmp/dockerforge_builds"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def build(self, dockerfile_content: str, repo_path: str) -> dict:
        """Write files, authenticate natively, build, and push to Hub."""
        
        # Tag the image for your specific Docker Hub repository
        tag_id = uuid.uuid4().hex[:8]
        full_tag = f"ujjawalraj123/dockerforge:{tag_id}"
        
        # 1. Write the Dockerfile
        df_path = Path(repo_path) / "Dockerfile"
        df_path.write_text(dockerfile_content)

        # 2. Write a default .dockerignore
        ignore_path = Path(repo_path) / ".dockerignore"
        if not ignore_path.exists():
            ignore_path.write_text(".git\nnode_modules\nvenv\n__pycache__\n*.pyc\n.env\n")

        # 3. Authenticate using environment variables
        docker_user = os.getenv("DOCKER_HUB_USER")
        docker_token = os.getenv("DOCKER_HUB_TOKEN")
        
        if docker_user and docker_token:
            print(f"[DockerRunner] Logging into Docker Hub as {docker_user}...")
            subprocess.run(
                ["docker", "login", "-u", docker_user, "--password-stdin"],
                input=docker_token,
                capture_output=True, text=True
            )
        else:
            print("[DockerRunner] WARNING: Docker Hub credentials not found in environment variables.")

        print(f"[DockerRunner] Building: docker build -t {full_tag} {repo_path}")
        
        # 4. Run the build
        build_result = subprocess.run(
            ["docker", "build", "-t", full_tag, repo_path],
            capture_output=True, 
            text=True, 
            timeout=900
        )
        
        stdout_log = build_result.stdout
        stderr_log = build_result.stderr
        success = build_result.returncode == 0

        # 5. If build succeeds, push it to Docker Hub
        if success:
            print(f"[DockerRunner] Build successful. Pushing to Hub: {full_tag}")
            push_result = subprocess.run(
                ["docker", "push", full_tag],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for uploading
            )
            
            stdout_log += f"\n\n--- DOCKER PUSH LOGS ---\n{push_result.stdout}"
            stderr_log += f"\n\n--- DOCKER PUSH ERRORS ---\n{push_result.stderr}"
            
            # If the push fails, mark the whole process as failed
            if push_result.returncode != 0:
                success = False

        return {
            "tag": full_tag,
            "success": success,
            "stdout": stdout_log,
            "stderr": stderr_log,
            "returncode": build_result.returncode if not success else push_result.returncode
        }

    def run(self, tag: str) -> dict:
        """Run the built container and verify it starts."""
        
        # Strip out slashes and colons so Docker doesn't crash on the container name
        safe_name = tag.replace("/", "-").replace(":", "-")
        
        print(f"[DockerRunner] Running: docker run --rm {tag}")
        result = subprocess.run(
            ["docker", "run", "--rm", "--detach",
             "--name", f"df-test-{safe_name}", tag],
            capture_output=True, text=True, timeout=60
        )
        
        # Stop it right after verification
        if result.returncode == 0:
            container_id = result.stdout.strip()
            subprocess.run(["docker", "stop", container_id],
                           capture_output=True, timeout=30)
                           
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }