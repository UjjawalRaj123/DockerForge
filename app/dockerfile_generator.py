from openai import OpenAI

class DockerfileGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate(self, repo_info: dict) -> str:
        """Generate a Dockerfile based on repo analysis."""

        structure_str = "\n".join(repo_info["structure"][:100])  # cap at 100 lines
        key_files_str = "\n\n".join(
            f"--- {fname} ---\n{content}"
            for fname, content in repo_info["key_files"].items()
        )

        prompt = f"""
You are an expert DevOps engineer. Analyze the following GitHub repository 
and generate a working, production-quality Dockerfile.

Repository name: {repo_info['repo_name']}

File structure:
{structure_str}

Key configuration files:
{key_files_str}

Requirements:
1. Detect the programming language and framework automatically.
2. Use an appropriate official base image (slim/alpine preferred).
3. Include all necessary install steps.
4. Set a correct CMD or ENTRYPOINT.
5. Use multi-stage build if appropriate.
6. Follow Docker best practices (non-root user, .dockerignore hints, layer caching).
7. CRITICAL FOR FRONTEND/MERN APPS: If the app has a build step (like React/Vite/Angular), make sure your final stage copies the compiled production folder (e.g., /build or /dist), NOT the raw /public folder.
8. Output ONLY the raw Dockerfile content — no explanation, no markdown fences.
"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        # Defensive string cleaning to prevent Docker parse errors
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```"):
            content = content.replace("```dockerfile\n", "")
            content = content.replace("```docker\n", "")
            content = content.replace("```\n", "")
            content = content.replace("```", "")
            
        return content.strip()