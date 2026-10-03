"""Minimal Clockify API client.

Raises instead of returning error responses so the sync layer can decide
whether a failure is worth retrying.
"""
import logging

import requests

BASE_URL = 'https://api.clockify.me/api/v1'


class ClockifyError(Exception):
    def __init__(self, status, text):
        super().__init__('HTTP %s: %s' % (status, (text or '')[:300]))
        self.status = status


class ClockifyClient:
    def __init__(self, api_key, timeout=10):
        self.timeout = timeout
        self.headers = {'Content-Type': 'application/json', 'X-Api-Key': api_key}

    def _request(self, method, path, expected, body=None):
        resp = requests.request(
            method, BASE_URL + path, headers=self.headers, json=body, timeout=self.timeout
        )
        if resp.status_code not in expected:
            raise ClockifyError(resp.status_code, resp.text)
        return resp.json()

    def create_entry(self, workspace_id, body):
        return self._request('POST', '/workspaces/%s/time-entries' % workspace_id, (201,), body)

    def update_entry(self, workspace_id, entry_id, body):
        return self._request(
            'PUT', '/workspaces/%s/time-entries/%s' % (workspace_id, entry_id), (200,), body
        )

    def get_in_progress(self, workspace_id):
        """Running entries, or None if the fetch failed.

        Callers must distinguish: [] means "nothing running", None means
        "don't trust this, leave local state alone".
        """
        try:
            return self._request(
                'GET', '/workspaces/%s/time-entries/status/in-progress' % workspace_id, (200,)
            ) or []
        except Exception as e:
            logging.warning("Could not fetch in-progress Clockify entries: %s", e)
            return None
