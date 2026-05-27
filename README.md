# 🐳 DockerForge — AI-Powered Dockerfile Generator

> An agentic AI tool that clones any public GitHub repo, analyzes its
> codebase, generates a working Dockerfile, builds it, auto-fixes errors,
> and verifies the container runs — all autonomously.

## 🚀 Quick Start (Docker)

```bash
# 1. Clone this repo
git clone https://github.com/yourusername/dockerforge.git
cd dockerforge

# 2. Build the DockerForge image
docker build -t dockerforge .

# 3. Run it  (mount Docker socket so the agent can run docker commands)
docker run --rm -it \
  -p 8501:8501 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e OPENAI_API_KEY=your_openai_key_here \
  dockerforge