import os
import shutil
from pathlib import Path
from git import Repo

class RepoAnalyzer:
    def __init__(self, clone_base: str = "/tmp/dockerforge_repos"):
        self.clone_base = Path(clone_base)
        self.clone_base.mkdir(parents=True, exist_ok=True)

    def clone_and_scan(self, github_url: str) -> dict:
        """Clone a public GitHub repo and scan its file structure."""
        repo_name = github_url.rstrip("/").split("/")[-1]
        clone_path = self.clone_base / repo_name

        # Clean previous clone if exists
        if clone_path.exists():
            shutil.rmtree(clone_path)

        print(f"[RepoAnalyzer] Cloning {github_url} ...")
        Repo.clone_from(github_url, clone_path)

        structure = self._scan_structure(clone_path)
        file_samples = self._read_key_files(clone_path)

        return {
            "repo_name": repo_name,
            "clone_path": str(clone_path),
            "structure": structure,
            "key_files": file_samples
        }

    def _scan_structure(self, path: Path, max_depth: int = 3) -> list:
        """Return a list of relative file paths (limited depth)."""
        files = []
        for p in sorted(path.rglob("*")):
            if ".git" in p.parts:
                continue
            rel = p.relative_to(path)
            depth = len(rel.parts)
            if depth <= max_depth:
                files.append(str(rel))
        return files

    def _read_key_files(self, path: Path) -> dict:
        """Read key indicator files to help LLM understand the project."""
        key_filenames = [
            "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
            "pom.xml", "build.gradle", "go.mod", "Cargo.toml",
            "composer.json", ".nvmrc", ".python-version",
            "Makefile", "setup.py", "setup.cfg", "README.md"
        ]
        contents = {}
        for fname in key_filenames:
            fpath = path / fname
            if fpath.exists():
                try:
                    contents[fname] = fpath.read_text(errors="ignore")[:2000]
                except Exception:
                    pass
        return contents