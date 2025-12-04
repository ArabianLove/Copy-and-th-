import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import requests
from src.github_lockdown import get_all_repos, make_repo_private, get_headers


class TestGithubLockdown(unittest.TestCase):
    def setUp(self):
        self.token = "dummy_token"

    def test_get_headers(self):
        headers = get_headers(self.token)
        self.assertEqual(headers["Authorization"], "token dummy_token")
        self.assertEqual(headers["Accept"], "application/vnd.github.v3+json")

    @patch("src.github_lockdown.requests.get")
    def test_get_all_repos_success(self, mock_get):
        # Mocking pagination: first call returns 2 repos, second call returns
        # empty list (end)
        mock_response_page1 = MagicMock()
        mock_response_page1.json.return_value = [
            {"name": "repo1", "owner": {"login": "user"}, "private": False},
            {"name": "repo2", "owner": {"login": "user"}, "private": True},
        ]
        mock_response_page1.raise_for_status.return_value = None

        mock_response_page2 = MagicMock()
        mock_response_page2.json.return_value = []
        mock_response_page2.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        repos = get_all_repos(self.token)
        self.assertEqual(len(repos), 2)
        self.assertEqual(repos[0]["name"], "repo1")
        self.assertEqual(repos[1]["name"], "repo2")
        self.assertEqual(mock_get.call_count, 2)

    @patch("src.github_lockdown.requests.patch")
    def test_make_repo_private_success(self, mock_patch):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        result = make_repo_private(self.token, "user", "repo1")
        self.assertTrue(result)
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(kwargs["json"], {"private": True})

    @patch("src.github_lockdown.requests.patch")
    def test_make_repo_private_failure(self, mock_patch):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.RequestException("API Error")
        )
        mock_patch.return_value = mock_response

        # Capture stdout to avoid cluttering test output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        result = make_repo_private(self.token, "user", "repo1")

        sys.stdout = sys.__stdout__

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
