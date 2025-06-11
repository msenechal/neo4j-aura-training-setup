# neo4j-aura-training-setup
Automate the creation + distribution of Neo4j Aura DBs for customer trainings/workshops
You need docker up and running !

Set .env:
```
AURA_CLIENT_ID=
AURA_CLIENT_SECRET=
AURA_TENANT_ID=
```

Optional change default config in config.py


As easy as running:

```shell
python main.py --mode=init --nb_instances=5 --name=MS_TRAINING_AUTOMATION_TEST --memory="4GB"
```


Examples:
```
# Create 5 training databases
python main.py --mode=init --nb_instances=5 --name=MS_TRAINING_AUTOMATION_TEST --memory="4GB"

# Add 3 more instances to existing setup
python main.py --mode=add --nb_instances=2 --name=MS_TRAINING_AUTOMATION_TEST --memory="4GB"

# Delete all databases from credentials file
python main.py --mode=delete

# Delete only databases with specific base name
python main.py --mode delete --name TRAINING
```

DO NOT STOP AT THIS POINT even if it says so:

We have received your export and it is currently being loaded into your Aura instance.
You can wait here, or abort this command and head over to the console to be notified of when your database is running.
Import progress (estimated)
....................  10%


example of db creds:

db_credentials.json:
{
  "MS_TRAINING_AUTOMATION_TEST-1": {
    "db_id": "xxxxxx",
    "connection_url": "neo4j+s://xxxxxx.databases.neo4j.io",
    "username": "neo4j",
    "password": "xxxxxx"
  }
},
{
  "MS_TRAINING_AUTOMATION_TEST-2": {
    "db_id": "xxxxxx",
    "connection_url": "neo4j+s://xxxxxx.databases.neo4j.io",
    "username": "neo4j",
    "password": "xxxxxx"
  }
},
{
  "MS_TRAINING_AUTOMATION_TEST-3": {
    "db_id": "xxxxxx",
    "connection_url": "neo4j+s://xxxxxx.databases.neo4j.io",
    "username": "neo4j",
    "password": "xxxxxx"
  }
},
{
  "MS_TRAINING_AUTOMATION_TEST-4": {
    "db_id": "xxxxxx",
    "connection_url": "neo4j+s://xxxxxx.databases.neo4j.io",
    "username": "neo4j",
    "password": "xxxxxx"
  }
},
{
  "MS_TRAINING_AUTOMATION_TEST-5": {
    "db_id": "xxxxxx",
    "connection_url": "neo4j+s://xxxxxx.databases.neo4j.io",
    "username": "neo4j",
    "password": "xxxxxx"
  }
},


