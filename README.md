Twitter Bot for InspiredBy Project

## Running
1. Spin up a [Neo4j Database](https://neo4j.com/try-neo4j/)
2. Create a .env file with Neo4j + Twitter creds, see .env.example for required keys
3. Spin up virtual env and run:
```terminal
source venv/bin/activate
pip3 install -r requirements.txt
python3 app.py 
```