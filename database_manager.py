import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from aura_client import AuraClient, AuraAPIError
from config import DEFAULT_CREDENTIALS_FILE

logger = logging.getLogger(__name__)

class DatabaseManager:
    
    def __init__(self):
        self.client = AuraClient()
    
    def create_databases_with_clones(self, nb_instances: int, name: str, 
                                   instance_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        if nb_instances < 1:
            raise ValueError("nb_instances must be at least 1")
        
        results = {}
        
        primary_db_name = f"{name}-1"
        logger.info(f"Creating primary database '{primary_db_name}'...")
        
        try:
            primary_db = self.client.create_database(primary_db_name, instance_config)
            results[primary_db_name] = primary_db
            
            if not self.client.wait_for_database_ready(primary_db["db_id"]):
                logger.error(f"Primary database '{primary_db_name}' failed to start")
                return results
            
            self._load_database_dump(primary_db)
            
            if nb_instances > 1:
                clone_results = self._create_clones(
                    primary_db["db_id"], name, 2, nb_instances, instance_config
                )
                results.update(clone_results)
                
        except AuraAPIError as e:
            logger.error(f"Failed to create primary database: {e}")
        
        return results
    
    def add_cloned_instances(self, nb_instances: int, base_name: str, 
                           instance_config: Dict[str, Any], 
                           credentials_file: str = DEFAULT_CREDENTIALS_FILE) -> Dict[str, Dict[str, Any]]:
        if nb_instances < 1:
            raise ValueError("nb_instances must be at least 1")
        
        existing_dbs = self._load_existing_credentials(credentials_file)
        if not existing_dbs:
            logger.error("No existing database credentials found. Run with --mode=init first.")
            return {}
        
        primary_db_name = f"{base_name}-1"
        if primary_db_name not in existing_dbs:
            logger.error(f"Primary database '{primary_db_name}' not found in credentials file.")
            return {}
        
        primary_db_id = existing_dbs[primary_db_name]["db_id"]
        logger.info(f"Found primary database '{primary_db_name}' with ID: {primary_db_id}")
        
        start_index = self._find_next_available_index(base_name, existing_dbs)
        
        results = dict(existing_dbs)
        
        clone_results = self._create_clones(
            primary_db_id, base_name, start_index, start_index + nb_instances - 1, instance_config
        )
        results.update(clone_results)
        
        return results
    
    def delete_all_instances(self, credentials_file: str = DEFAULT_CREDENTIALS_FILE, 
                           confirm: bool = True, base_name: Optional[str] = None) -> bool:
        databases = self._load_existing_credentials(credentials_file)
        
        if not databases:
            logger.warning(f"No database credentials found in '{credentials_file}'")
            return False
        
        if base_name:
            filtered_databases = {
                name: creds for name, creds in databases.items()
                if name.startswith(f"{base_name}-")
            }
            if filtered_databases:
                databases = filtered_databases
                logger.info(f"Filtering databases by base name '{base_name}': {len(databases)} found")
            else:
                logger.warning(f"No databases found with base name '{base_name}'")
                return False
        
        results = self.client.batch_delete_databases(databases, confirm)
        
        if any(results.values()):
            remaining_databases = {
                name: creds for name, creds in databases.items()
                if name not in results or not results[name]
            }
            
            if base_name:
                original_databases = self._load_existing_credentials(credentials_file)
                for name, creds in original_databases.items():
                    if not name.startswith(f"{base_name}-"):
                        remaining_databases[name] = creds
            
            try:
                if remaining_databases:
                    self.store_credentials(remaining_databases, credentials_file)
                    logger.info(f"Updated credentials file: {len(remaining_databases)} databases remaining")
                else:
                    os.remove(credentials_file)
                    logger.info(f"Removed empty credentials file '{credentials_file}'")
            except Exception as e:
                logger.error(f"Failed to update credentials file: {e}")
        
        success_count = sum(results.values())
        total_count = len(results)
        return success_count == total_count
    
    def _create_clones(self, source_db_id: str, base_name: str, start_index: int, 
                      end_index: int, instance_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        results = {}
        
        for i in range(start_index, end_index + 1):
            clone_name = f"{base_name}-{i}"
            logger.info(f"Creating clone '{clone_name}'...")
            
            try:
                clone_info = self.client.create_database(
                    clone_name, instance_config, source_db_id
                )
                results[clone_name] = clone_info
                
            except AuraAPIError as e:
                logger.error(f"Failed to create clone '{clone_name}': {e}")
                continue
        
        return results
    
    def _load_database_dump(self, db_info: Dict[str, Any]) -> None:
        dump_path = Path.cwd() / "dumps"
        
        if not dump_path.exists():
            logger.warning(f"Dump directory '{dump_path}' not found. Skipping data load.")
            return
        
        docker_command = (
            f'docker run --rm -v {dump_path}:/dumps '
            f'neo4j:2025.04.0-enterprise '
            f'bash -c "'
            f'./bin/neo4j-admin database upload neo4j '
            f'--from-path=/dumps '
            f'--to-uri=neo4j+s://{db_info["db_id"]}.databases.neo4j.io '
            f'--overwrite-destination=true '
            f'--to-password={db_info["password"]} '
            f'--to-user=neo4j"'
        )
        
        logger.info(f"Loading dump into database {db_info['db_id']}...")
        logger.debug(f"Docker command: {docker_command}")
        
        exit_code = os.system(docker_command)
        if exit_code == 0:
            logger.info("Database dump loaded successfully")
        else:
            logger.error(f"Failed to load database dump (exit code: {exit_code})")
    
    def _load_existing_credentials(self, credentials_file: str) -> Dict[str, Dict[str, Any]]:
        try:
            with open(credentials_file, "r") as file:
                content = file.read().strip()
                if not content:
                    return {}
                
                if content.startswith("{") and content.endswith("}"):
                    return json.loads(content)
                else:
                    content = "[" + content.rstrip(",\n") + "]"
                    existing_dbs = {}
                    for item in json.loads(content):
                        existing_dbs.update(item)
                    return existing_dbs
                
        except FileNotFoundError:
            logger.warning(f"Credentials file '{credentials_file}' not found")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in credentials file: {e}")
            return {}
    
    def _find_next_available_index(self, base_name: str, existing_dbs: Dict[str, Any]) -> int:
        index = 1
        while f"{base_name}-{index}" in existing_dbs:
            index += 1
        return index
    
    def store_credentials(self, databases: Dict[str, Dict[str, Any]], 
                         filename: str = DEFAULT_CREDENTIALS_FILE) -> None:
        try:
            credentials_data = {}
            for db_name, creds in databases.items():
                credentials_data[db_name] = {
                    "db_id": creds["db_id"],
                    "connection_url": creds["connection_url"],
                    "username": creds["username"],
                    "password": creds["password"]
                }
            
            with open(filename, "w") as file:
                json.dump(credentials_data, file, indent=2)
            
            logger.info(f"Stored credentials for {len(databases)} databases in '{filename}'")
            
        except IOError as e:
            logger.error(f"Failed to store credentials: {e}")
            raise