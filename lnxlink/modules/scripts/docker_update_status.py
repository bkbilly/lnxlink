"""Checks for updates on selected docker images"""

import os
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import quote_plus
import asyncio
import aiohttp

# --- Configuration ---
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
QUAY_TOKEN = os.getenv("QUAY_TOKEN")


# --- Registry Clients ---


class RegistryClient:
    """Base class for a registry client."""

    def __init__(self, repo: str, session: aiohttp.ClientSession):
        self.repo = repo
        self.session = session
        self.base_url = ""

    async def get_remote_digest(self, tag: str) -> Optional[str]:
        """Fetches the manifest for a tag and returns its digest."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @staticmethod
    def parse_repo_name(image_name: str) -> Tuple[str, str, str]:
        """Parses an image name into (registry, repository, tag)."""
        if ":" not in image_name:
            image_name += ":latest"
        registry_part, tag = image_name.rsplit(":", 1)
        parts = registry_part.split("/")
        registry = "docker.io"
        if "." in parts[0] and len(parts) > 1:
            registry = parts[0]
            repository = "/".join(parts[1:])
        else:
            repository = registry_part
            if "/" not in repository:
                repository = f"library/{repository}"
        return registry, repository, tag


class DockerHubClient(RegistryClient):
    """Client for Docker Hub."""

    def __init__(self, repo: str, session: aiohttp.ClientSession):
        super().__init__(repo, session)
        self.auth_url = "https://auth.docker.io/token?service=registry.docker.io"
        self.base_url = "https://registry-1.docker.io/v2"

    async def _get_auth_token(self) -> str:
        url = f"{self.auth_url}&scope=repository:{self.repo}:pull"
        async with self.session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return data["token"]

    async def get_remote_digest(self, tag: str) -> Optional[str]:
        try:
            token = await self._get_auth_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.index.v1+json",  # noqa: E501
            }
            url = f"{self.base_url}/{self.repo}/manifests/{tag}"
            async with self.session.head(url, headers=headers) as response:
                response.raise_for_status()
                return response.headers.get("Docker-Content-Digest")
        except aiohttp.ClientError:
            return None


class GhcrClient(RegistryClient):
    """Client for GitHub Container Registry (ghcr.io)."""

    def __init__(self, repo: str, session: aiohttp.ClientSession):
        super().__init__(repo, session)
        self.base_url = "https://ghcr.io/v2"
        self.token_url = (
            f"https://ghcr.io/token?service=ghcr.io&scope=repository:{self.repo}:pull"
        )

    async def _get_anonymous_token(self) -> Optional[str]:
        """Fetches a temporary public token for GHCR."""
        try:
            async with self.session.get(self.token_url) as response:
                response.raise_for_status()
                data = await response.json()
                return data["token"]
        except aiohttp.ClientError:
            return None

    async def get_remote_digest(self, tag: str) -> Optional[str]:
        headers = {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.index.v1+json"  # noqa: E501
        }
        token = await self._get_anonymous_token()
        if not token:
            # We return None and let the caller decide how to report the error
            return None
        headers["Authorization"] = f"Bearer {token}"
        try:
            url = f"{self.base_url}/{self.repo}/manifests/{tag}"
            async with self.session.head(url, headers=headers) as response:
                response.raise_for_status()
                return response.headers.get("Docker-Content-Digest")
        except aiohttp.ClientError:
            return None


class LscrClient(GhcrClient):
    """Client for LinuxServer Container Registry (lscr.io)."""

    def __init__(self, repo: str, session: aiohttp.ClientSession):
        super().__init__(repo, session)
        self.base_url = "https://lscr.io/v2"


class QuayClient(RegistryClient):
    """Client for Quay.io."""

    def __init__(self, repo: str, session: aiohttp.ClientSession):
        super().__init__(repo, session)
        self.base_url = "https://quay.io/api/v1"

    async def get_remote_digest(self, tag: str) -> Optional[str]:
        headers = {"Accept": "application/json"}
        if QUAY_TOKEN:
            headers["Authorization"] = f"Bearer {QUAY_TOKEN}"
        try:
            url = f"{self.base_url}/repository/{self.repo}/tag/{tag}"
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("manifest_digest")
        except aiohttp.ClientError:
            return None


class GitLabClient(RegistryClient):
    """Client for GitLab Container Registry."""

    def __init__(self, repo: str, session: aiohttp.ClientSession):
        super().__init__(repo, session)
        self.base_url = "https://gitlab.com/api/v4"
        self._project_id = None

    async def _get_project_id(self) -> Optional[str]:
        if self._project_id:
            return self._project_id
        if not GITLAB_TOKEN:
            return None
        project_path = (
            "/".join(self.repo.split("/")[:-1]) if "/" in self.repo else self.repo
        )
        try:
            headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
            encoded_project_path = quote_plus(project_path)
            url = f"{self.base_url}/projects/{encoded_project_path}"
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                self._project_id = data["id"]
                return self._project_id
        except aiohttp.ClientError:
            return None

    async def get_remote_digest(self, tag: str) -> Optional[str]:
        project_id = await self._get_project_id()
        if not project_id:
            return None
        try:
            headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
            repo_url = f"{self.base_url}/projects/{project_id}/registry/repositories"
            async with self.session.get(repo_url, headers=headers) as repo_response:
                repo_response.raise_for_status()
                repos_data = await repo_response.json()
                repo_id = next(
                    (repo["id"] for repo in repos_data if repo["path"] == self.repo),
                    None,
                )
            if not repo_id:
                return None
            tag_url = f"{self.base_url}/projects/{project_id}/registry/repositories/{repo_id}/tags/{tag}"
            async with self.session.get(tag_url, headers=headers) as tag_response:
                tag_response.raise_for_status()
                tag_data = await tag_response.json()
                return tag_data["digest"]
        except aiohttp.ClientError:
            return None


class DockerUpdateStatus:
    """docstring for DockerUpdateStatus"""

    def get_registry_client(
        self, registry: str, repo: str, session: aiohttp.ClientSession
    ) -> Optional[RegistryClient]:
        """Factory function to return the appropriate client for a given registry."""
        if registry == "docker.io":
            return DockerHubClient(repo, session)
        if registry == "ghcr.io":
            return GhcrClient(repo, session)
        if registry == "lscr.io":
            return LscrClient(repo, session)
        if registry == "quay.io":
            return QuayClient(repo, session)
        if registry.endswith("gitlab.com"):
            return GitLabClient(repo, session)
        return None

    # pylint: disable=no-else-return
    async def check_image_tag(
        self,
        full_tag: str,
        image_id: str,
        repo_digests: List[str],
        session: aiohttp.ClientSession,
    ) -> Dict[str, Any]:
        """
        Checks a single image tag and returns a result dictionary.
        """
        try:
            registry, repo, tag = RegistryClient.parse_repo_name(full_tag)
            local_digest = ""
            if repo_digests:
                for d in repo_digests:
                    if d.startswith(repo) or d.startswith(f"{registry}/{repo}"):
                        local_digest = d.split("@")[1]
                        break
            if not local_digest:
                local_digest = image_id

            client = self.get_registry_client(registry, repo, session)
            if not client:
                return {
                    "tag": full_tag,
                    "status": "error",
                    "message": f"Unsupported registry: {registry}",
                }

            remote_digest = await client.get_remote_digest(tag)

            if not remote_digest:
                return {
                    "tag": full_tag,
                    "status": "error",
                    "message": "Could not fetch remote digest.",
                }
            elif local_digest.strip() == remote_digest.strip():
                return {
                    "tag": full_tag,
                    "status": "up_to_date",
                }
            else:
                return {
                    "tag": full_tag,
                    "status": "update_available",
                    "local": local_digest,
                    "remote": remote_digest,
                }
        except Exception as e:
            return {
                "tag": full_tag,
                "status": "error",
                "message": str(e),
            }

    async def get_updates(self, images):
        """Checks for updates async"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for image in images:
                if not image.tags:
                    continue
                for tag in image.tags:
                    task = self.check_image_tag(
                        tag, image.id, image.attrs.get("RepoDigests", []), session
                    )
                    tasks.append(task)

            all_results = await asyncio.gather(*tasks)

        return all_results

    def get_updates_sync(self, images):
        """Run the get_updates synchronously"""
        return asyncio.run(self.get_updates(images))
