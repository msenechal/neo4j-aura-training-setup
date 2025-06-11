import os
from dotenv import load_dotenv

load_dotenv()

AURA_CLIENT_ID = os.getenv("AURA_CLIENT_ID")
AURA_CLIENT_SECRET = os.getenv("AURA_CLIENT_SECRET")
AURA_TENANT_ID = os.getenv("AURA_TENANT_ID")
AURA_API_BASE = "https://api.neo4j.io/v1"
OAUTH_TOKEN_URL = "https://api.neo4j.io/oauth/token"

DEFAULT_INSTANCE_CONFIG = {
    "version": "5",
    "region": "europe-west1",
    "memory": "2GB",
    "type": "enterprise-db",
    "cloud_provider": "gcp"
}

DEFAULT_MAX_RETRIES = 30
DEFAULT_RETRY_INTERVAL = 10
DEFAULT_CREDENTIALS_FILE = "db_credentials.json"

def validate_environment():
    missing = []
    if not AURA_CLIENT_ID:
        missing.append("AURA_CLIENT_ID")
    if not AURA_CLIENT_SECRET:
        missing.append("AURA_CLIENT_SECRET")
    if not AURA_TENANT_ID:
        missing.append("AURA_TENANT_ID")
    
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")