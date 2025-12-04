import os
import sys
import requests
from typing import List, Dict, Any


def get_headers(token: str) -> Dict[str, str]:
    """
    Constructs the headers for GitHub API requests.

    Args:
        token (str): The GitHub Personal Access Token.

    Returns:
        Dict[str, str]: A dictionary containing the Authorization and
        Accept headers.
    """
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_all_repos(token: str) -> List[Dict[str, Any]]:
    """
    Fetches all repositories for the authenticated user, handling pagination.

    Args:
        token (str): The GitHub Personal Access Token.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each
        dictionary represents a repository.
    """
    headers = get_headers(token)
    repos = []
    page = 1
    per_page = 100
    base_url = "https://api.github.com/user/repos"

    print("Fetching repository list...")
    while True:
        try:
            params = {"type": "owner", "page": page, "per_page": per_page}
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            if not data:
                break

            repos.extend(data)
            print(f"  Fetched page {page} ({len(data)} repos)")
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            sys.exit(1)

    return repos


def make_repo_private(token: str, owner: str, repo_name: str) -> bool:
    """
    Sets the visibility of a specific repository to private.

    Args:
        token (str): The GitHub Personal Access Token.
        owner (str): The owner of the repository.
        repo_name (str): The name of the repository.

    Returns:
        bool: True if successful or already private, False otherwise.
    """
    headers = get_headers(token)
    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    payload = {"private": True}

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"[SUCCESS] {owner}/{repo_name} is now private.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to update {owner}/{repo_name}: {e}")
        return False


def main() -> None:
    """
    Main execution function.
    """
    print("--- GITHUB REPOSITORY LOCKDOWN PROTOCOL ---")
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        print("Please export GITHUB_TOKEN='your_token_here' and try again.")
        sys.exit(1)

    repos = get_all_repos(token)
    print(f"Total repositories found: {len(repos)}")

    confirm = input(
        "Are you sure you want to make ALL these repositories private? "
        "(yes/no): "
    )
    if confirm.lower() != "yes":
        print("Operation aborted.")
        sys.exit(0)

    for repo in repos:
        name = repo.get("name")
        owner = repo.get("owner", {}).get("login")
        private = repo.get("private")

        if not name or not owner:
            print(f"Skipping malformed repo data: {repo}")
            continue

        if private:
            print(f"[SKIP] {owner}/{name} is already private.")
        else:
            make_repo_private(token, owner, name)

    print("Lockdown complete.")


if __name__ == "__main__":
    main()
