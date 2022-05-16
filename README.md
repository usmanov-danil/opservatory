# Opservatory

API for checking docker containers states in a small infrastructure

## Quick start

Step 1.0  Put Ansible hosts file into inventory

`opservatory/infrastructure/inventory/` <- file named hosts should be here

Step 1.5  Replace company name in config.json

Step 2.0  Run locally

```
uvicorn opservatory.api:app --host 0.0.0.0 --port 5000
```

or 

```
docker build -t opservatory .
docker run -p 5000:5000 opservatory
```

---

Made by [Subatiq](https://github.com/subatiq) for the team of Edge Vision
