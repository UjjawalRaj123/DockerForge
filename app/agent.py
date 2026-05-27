from repo_analyzer import RepoAnalyzer
from dockerfile_generator import DockerfileGenerator
from docker_runner import DockerRunner
from openai import OpenAI

class DockerForgeAgent:
    MAX_RETRIES = 3

    def __init__(self, api_key: str):
        self.analyzer = RepoAnalyzer()
        self.generator = DockerfileGenerator(api_key)
        self.runner = DockerRunner()
        self.client = OpenAI(api_key=api_key)

    def run(self, github_url: str, log_callback=None):
        """
        Full agentic loop:
        Steps 1-7 as per DockerForge specification.
        """
        def log(msg):
            if log_callback:
                log_callback(msg)
            print(msg)

        # ── Step 1 & 2: Clone and scan ──────────────────────────────
        log("📦 Step 1-2: Cloning repository and scanning file structure...")
        repo_info = self.analyzer.clone_and_scan(github_url)
        log(f"✅ Cloned '{repo_info['repo_name']}' "
            f"— {len(repo_info['structure'])} files found.")

        dockerfile = None
        build_result = None
        attempt = 0

        while attempt < self.MAX_RETRIES:
            attempt += 1
            log(f"\n🤖 Step 3 (Attempt {attempt}/{self.MAX_RETRIES}): "
                f"Generating Dockerfile with AI...")

            # ── Step 3: Generate Dockerfile ─────────────────────────
            if attempt == 1:
                dockerfile = self.generator.generate(repo_info)
            else:
                # ── Step 5: Reason about failure and fix ───────────
                log(f"🔧 Step 5: Build failed — asking AI to fix the error...")
                dockerfile = self._fix_dockerfile(
                    dockerfile,
                    build_result["stderr"] + build_result["stdout"]
                )

            log("📄 Dockerfile generated.")

            # ── Step 4: docker build ────────────────────────────────
            log(f"🔨 Step 4: Running docker build...")
            build_result = self.runner.build(dockerfile, repo_info["clone_path"])

            if build_result["success"]:
                log("✅ docker build succeeded!")
                break
            else:
                log(f"❌ Build failed (attempt {attempt}):\n"
                    f"{build_result['stderr'][-500:]}")

        if not build_result["success"]:
            log("🚨 All retry attempts exhausted. Returning best Dockerfile.")
            return {
                "success": False,
                "dockerfile": dockerfile,
                "build_output": build_result,
                "run_output": None
            }

        # ── Step 6: docker run ──────────────────────────────────────
        log("\n🚀 Step 6: Running container to verify it starts...")
        run_result = self.runner.run(build_result["tag"])

        if run_result["success"]:
            log("✅ Container started and responded successfully!")
        else:
            log(f"⚠️ Container run check: {run_result['stderr'][:300]}")

        # ── Step 7: Return final result ─────────────────────────────
        log("\n🎉 Step 7: Final working Dockerfile ready!")
        return {
            "success": True,
            "dockerfile": dockerfile,
            "build_output": build_result,
            "run_output": run_result
        }

    def _fix_dockerfile(self, original: str, error_log: str) -> str:
        """Ask the LLM to fix a broken Dockerfile given the error output."""
        prompt = f"""
The following Dockerfile failed to build. 
Analyze the error and return a corrected Dockerfile.

--- Original Dockerfile ---
{original}

--- Build Error ---
{error_log[-2000:]}

Output ONLY the corrected raw Dockerfile — no markdown, no explanation.
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()