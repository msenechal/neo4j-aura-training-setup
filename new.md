# Neo4j Aura Training Setup

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Local_docker_runtime-blue.svg)](https://www.python.org/downloads/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Aura-green.svg)](https://neo4j.com/cloud/aura/)

Automate the creation, management, and distribution of Neo4j Aura databases for customer trainings and workshops. This tool streamlines the process of spinning up multiple Neo4j graph database instances with pre-loaded data.

## 🚀 Features

- **Bulk Database Creation**: Create multiple Neo4j Aura instances with a single command
- **Scaling**: Adding new cloned instances with a single command to dynamically scale if more instances are needed.
- **Seeding**: Load custom dumps/backups into databases using Docker
- **Bulk Delete**: Delete specific database groups/workshops in a bulk
- **Credential Management**: Automatic generation and storage of connection credentials
- **Multi-cloud Support**: Support for GCP, AWS, and Azure deployments in your Aura tenant
- **Configurable Resources**: Specify memory, region, and database type per your needs

## 📋 Prerequisites

- **Python 3.7+**
- **Docker** (must be running for data seeding functionality)
- **Neo4j Aura API Credentials** (Client ID, Client Secret, Tenant ID)
- **Custom database dumps** (named `neo4j.dump` place in `/dumps` directory)

## 🛠 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/msenechal/neo4j-aura-training-setup
   cd neo4j-aura-training-setup
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your Aura credentials:
   ```env
   AURA_CLIENT_ID=your_client_id_here
   AURA_CLIENT_SECRET=your_client_secret_here
   AURA_TENANT_ID=your_tenant_id_here
   ```

3. **Prepare your data**:
   - Create a `dumps` directory in the project root
   - Place your Neo4j database dump/backups in this directory with the name: `neo4j.dump`
   - The tool will automatically load this data into the instances

## 💡 Usage

### Basic Commands

#### Create Training Databases
```bash
# Create 5 training databases with 4GB memory each
python main.py --mode=init --nb_instances=5 --name=MS_WORKSHOP_CustomerName_June_2025 --memory="4GB"
```

#### Add More Instances
```bash
# Add 3 more instances to existing setup
python main.py --mode=add --nb_instances=3 --name=MS_WORKSHOP_CustomerName_June_2025 --memory="4GB"
```

#### Delete Databases
```bash
# Delete all databases from credentials file without asking confirmation
python main.py --mode=delete --force

# Delete only databases with specific base name
python main.py --mode=delete --name=MS_WORKSHOP_CustomerName_June_2025
```

### Advanced Configuration

#### All Available Options
```bash
python main.py \
  --mode=init \
  --nb_instances=10 \
  --name=MS_WORKSHOP_CustomerName_June_2025 \
  --memory="8GB" \
  --region="us-central1" \
  --cloud_provider="gcp" \
  --type="enterprise-db" \
  --version="5" \
  --output_file="my_credentials.json" \
  --log_level="DEBUG"
```

#### Parameter Reference
| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `--mode` | Operation mode | `init` | `init`, `add`, `delete` |
| `--nb_instances` | Number of instances to create | `1` | Any positive integer |
| `--name` | Base name for databases | `TRAINING` | Any string |
| `--memory` | Memory allocation | `2GB` | `2GB`, `4GB`, `8GB`, `16GB`, `32GB`, `...` |
| `--region` | Cloud region | `europe-west1` | Valid cloud regions |
| `--cloud_provider` | Cloud provider | `gcp` | `gcp`, `aws`, `azure` |
| `--type` | Database type | `enterprise-db` | `free-db`, `professional-db`, `enterprise-db`, `business-critical` |
| `--version` | Neo4j version | `5` | `4`, `5` |
| `--output_file` | Credentials output file | `db_credentials.json` | Any filename |
| `--log_level` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `--force` | Skip confirmations | `False` | Flag (no value) |

## 📁 Project Structure

```
neo4j-aura-training-setup/
├── main.py                 # Main application entry point
├── aura_client.py          # Neo4j Aura API client
├── database_manager.py     # Database operations manager
├── config.py              # Configuration and environment setup
├── dumps/                 # Directory for database dumps (optional)
├── db_credentials.json    # Generated credentials file
├── aura_setup.log        # Application logs
├── .env                  # Environment variables
├── .env.example          # Environment template
└── README.md            # This file
```

## 📊 Output Format

The tool generates a `db_credentials.json` file with connection details:

```json
{
  "MS_WORKSHOP_CustomerName_June_2025-1": {
    "db_id": "abc123",
    "connection_url": "neo4j+s://abc123.databases.neo4j.io",
    "username": "neo4j",
    "password": "generated_password"
  },
  "MS_WORKSHOP_CustomerName_June_2025-2": {
    "db_id": "def456",
    "connection_url": "neo4j+s://def456.databases.neo4j.io",
    "username": "neo4j",
    "password": "generated_password"
  }
}
```

## ⚡ How It Works

1. **Primary Database Creation**: Creates the first database instance with your specified configuration
2. **Data Loading**: Loads custom data using neo4j-admin in a docker container
3. **Cloning Process**: Creates additional instances by cloning the primary database to get to the requested number of instances
4. **Credential Storage**: Saves all connection details to a JSON file for easy distribution

> **⚠️ Important**: Do not stop the process when you see "We have received your export..." message. The data loading process can take 5-10 minutes depending on your dump size.

## 🔧 Troubleshooting

### Logging

Enable debug logging for detailed troubleshooting:
```bash
python main.py --log_level=DEBUG --mode=init --nb_instances=1 --name=DEBUG_TEST
```

Logs are written to both console and `aura_setup.log` file.

## 🔮 Roadmap

- [ ] **Bulk pause/resume functionality** for cost management during multi-day workshops
- [ ] **Custom seed/dump specification** via `--seed` parameter
- [ ] **Cypher-based data loading** when multi-DB support becomes available in Aura

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Issues

- Create an issue for bug reports or feature requests
- Share the logs in `aura_setup.log` for debugging

---

**Happy Training! 🎓**

