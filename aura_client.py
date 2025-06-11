import time
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Optional, Any, List
import logging

from config import (
    AURA_CLIENT_ID, AURA_CLIENT_SECRET, AURA_TENANT_ID,
    AURA_API_BASE, OAUTH_TOKEN_URL, DEFAULT_MAX_RETRIES, DEFAULT_RETRY_INTERVAL
)

logger = logging.getLogger(__name__)

class AuraAPIError(Exception):
    pass

class AuraClient:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_access_token(self) -> str:
        current_time = time.time()
        if self._access_token and current_time < (self._token_expires_at - 300):
            return self._access_token

        try:
            response = requests.post(
                OAUTH_TOKEN_URL,
                data={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=HTTPBasicAuth(AURA_CLIENT_ID, AURA_CLIENT_SECRET),
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = current_time + expires_in

            return self._access_token

        except requests.RequestException as e:
            raise AuraAPIError(f"Failed to get access token: {e}")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }

    def create_database(self, name: str, instance_config: Dict[str, Any], 
                       source_instance_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "name": name,
            "tenant_id": AURA_TENANT_ID,
            **instance_config
        }

        if source_instance_id:
            payload["source_instance_id"] = source_instance_id

        try:
            response = requests.post(
                f"{AURA_API_BASE}/instances",
                json=payload,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            db_info = response.json()["data"]
            logger.info(f"{'Cloned' if source_instance_id else 'Created'} database '{name}' with ID: {db_info['id']}")

            return {
                "db_id": db_info["id"],
                "connection_url": db_info["connection_url"],
                "username": db_info["username"],
                "password": db_info["password"]
            }

        except requests.RequestException as e:
            error_msg = f"Failed to {'clone' if source_instance_id else 'create'} database '{name}': {e}"
            logger.error(error_msg)
            raise AuraAPIError(error_msg)

    def get_database_status(self, db_id: str) -> str:
        try:
            response = requests.get(
                f"{AURA_API_BASE}/instances/{db_id}",
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()["data"]["status"]

        except requests.RequestException as e:
            raise AuraAPIError(f"Failed to get status for database {db_id}: {e}")

    def delete_database(self, db_id: str, db_name: str) -> bool:
        try:
            response = requests.delete(
                f"{AURA_API_BASE}/instances/{db_id}",
                headers=self._get_headers(),
                timeout=30
            )

            if response.status_code == 202:
                logger.info(f"✅ Successfully deleted database '{db_name}' (ID: {db_id})")
                return True
            else:
                logger.error(f"❌ Failed to delete database '{db_name}' (ID: {db_id}). Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"❌ Error deleting database '{db_name}' (ID: {db_id}): {e}")
            return False

    def batch_delete_databases(self, databases: Dict[str, Dict[str, Any]], 
                              confirm: bool = True) -> Dict[str, bool]:
        if not databases:
            logger.warning("No databases to delete")
            return {}

        logger.info(f"Found {len(databases)} databases to delete:")
        for db_name in databases.keys():
            logger.info(f"  - {db_name}")

        if confirm:
            response = input("\nAre you sure you want to delete these databases? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Delete cancelled")
                return {}

        results = {}
        success_count = 0

        for db_name, creds in databases.items():
            db_id = creds.get('db_id')
            if not db_id:
                logger.error(f"No database ID found for '{db_name}', skipping")
                results[db_name] = False
                continue

            success = self.delete_database(db_id, db_name)
            results[db_name] = success
            if success:
                success_count += 1

        logger.info(f"✅ Successfully deleted {success_count}/{len(databases)} databases")
        return results

    def wait_for_database_ready(self, db_id: str, max_retries: int = DEFAULT_MAX_RETRIES,
                               retry_interval: int = DEFAULT_RETRY_INTERVAL) -> bool:
        logger.info(f"Waiting for database {db_id} to be ready...")

        for attempt in range(max_retries):
            try:
                status = self.get_database_status(db_id)
                logger.info(f"Database {db_id} status: {status} (attempt {attempt + 1}/{max_retries})")

                if status == "running":
                    logger.info(f"Database {db_id} is now running")
                    return True

                if status in ["failed", "error"]:
                    logger.error(f"Database {db_id} failed to start")
                    return False

                time.sleep(retry_interval)

            except AuraAPIError as e:
                logger.error(f"Error checking database status: {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(retry_interval)

        logger.error(f"Database {db_id} did not reach 'running' status within {max_retries} attempts")
        return False