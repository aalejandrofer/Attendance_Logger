"""Best-effort Supabase mirror over the PostgREST HTTP API.

Talks REST directly (not supabase-py) because the client version on the Pi
has no `on_conflict` for upserts, and the device only needs three calls.
Every method raises on failure; the sync layer decides what to do.
"""
import requests


class SupabaseMirror:
    def __init__(self, url, key, timeout=10):
        self.base = url.rstrip('/') + '/rest/v1'
        self.timeout = timeout
        self.headers = {
            'apikey': key,
            'Authorization': 'Bearer ' + key,
            'Content-Type': 'application/json',
        }

    def _check(self, resp):
        if resp.status_code >= 300:
            raise RuntimeError('Supabase HTTP %s: %s' % (resp.status_code, resp.text[:300]))
        return resp

    def upsert(self, table, rows, on_conflict):
        if not rows:
            return
        headers = dict(self.headers, Prefer='resolution=merge-duplicates,return=minimal')
        self._check(requests.post(
            '%s/%s' % (self.base, table), params={'on_conflict': on_conflict},
            headers=headers, json=rows, timeout=self.timeout,
        ))

    def fetch_cards(self):
        resp = self._check(requests.get(
            self.base + '/projects',
            params={'select': 'tag_uuid,name,user_id,project_id,workspace_id,task_id'},
            headers=self.headers, timeout=self.timeout,
        ))
        return resp.json()

    def delete_card(self, tag_uuid):
        self._check(requests.delete(
            self.base + '/projects', params={'tag_uuid': 'eq.' + tag_uuid},
            headers=self.headers, timeout=self.timeout,
        ))

    def ping(self):
        self._check(requests.get(
            self.base + '/projects', params={'select': 'tag_uuid', 'limit': '1'},
            headers=self.headers, timeout=self.timeout,
        ))
