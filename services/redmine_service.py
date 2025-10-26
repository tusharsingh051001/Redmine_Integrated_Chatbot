import logging
from typing import Dict, List, Optional
import requests
import httpx

logger = logging.getLogger(__name__)


class RedmineService:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-Redmine-API-Key': api_key,
            'Content-Type': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return {'success': True}
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Redmine API error: {e}")
            raise

    # ------------------ Issues ------------------
    def get_issues(self, assigned_to_id: str = 'me', status_id: str = 'open',
                   project_id: Optional[str] = None, limit: int = 25):
        params = {'assigned_to_id': assigned_to_id, 'status_id': status_id, 'limit': limit}
        if project_id:
            params['project_id'] = project_id
        return self._make_request('GET', 'issues.json', params=params)

    def get_issue(self, issue_id: int, include: List[str] = None):
        params = {}
        if include:
            params['include'] = ','.join(include)
        return self._make_request('GET', f'issues/{issue_id}.json', params=params)

    def create_issue(self, issue_data: Dict):
        return self._make_request('POST', 'issues.json', json={'issue': issue_data})

    def update_issue(self, issue_id: int, issue_data: Dict):
        return self._make_request('PUT', f'issues/{issue_id}.json', json={'issue': issue_data})

    # ------------------ Projects ------------------
    def get_projects(self, limit: int = 100):
        return self._make_request('GET', 'projects.json', params={'limit': limit})

    def get_project(self, project_id: str, include: List[str] = None):
        params = {}
        if include:
            params['include'] = ','.join(include)
        return self._make_request('GET', f'projects/{project_id}.json', params=params)

    # ------------------ Trackers ------------------
    def get_trackers(self):
        return self._make_request('GET', 'trackers.json')

    # ------------------ Time Entries ------------------
    async def get_time_entry_activities(self):
        url = f"{self.base_url}/enumerations/time_entry_activities.json"
        async with httpx.AsyncClient() as client:
            logger.info(f"[Redmine] GET {url}")
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def create_time_entry(self, data: dict):
        url = f"{self.base_url}/time_entries.json"
        payload = {"time_entry": data}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_time_entries(self, user_id="me", from_date=None, to_date=None):
        url = f"{self.base_url}/time_entries.json"
        params = {"user_id": user_id}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def update_time_entry(self, entry_id: int, time_entry_data: Dict):
        url = f"{self.base_url}/time_entries/{entry_id}.json"
        payload = {"time_entry": time_entry_data}
        async with httpx.AsyncClient() as client:
            resp = await client.put(url, headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    # ------------------ Helpers ------------------
    def get_current_user(self):
        return self._make_request('GET', 'users/current.json')

    def get_issue_statuses(self):
        return self._make_request('GET', 'issue_statuses.json')
