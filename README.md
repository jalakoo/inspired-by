Twitter Bot for Neo4j InspiredBy Project

## Deployment
Targeted for deployment as a Google Cloud Function

## Local Running
1. Spin up a [Neo4j Database](https://neo4j.com/try-neo4j/)
2. Create a .env file with Neo4j + Twitter creds, see .env.example for required keys
3. Spin up virtual env and run:
```terminal
source venv/bin/activate
pip3 install -r requirements.txt
python3 main.py 
```

## Local GCF Testing
In console:
1. `pip install functions-framework`
2. `functions_framework --target=YOUR_FUNCTION_NAME`

Then hit the locally generated endpoint (port 8080 is default)
`curl http://localhost:8080`

Can also explicitly assign port like:
`functions_framework --target=YOUR_FUNCTION_NAME --port:7878`

[Official documentation](https://cloud.google.com/functions/docs/running/function-frameworks)
