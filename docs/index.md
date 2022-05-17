# Opservatory

![](brands/full_logo.svg)


A small deployable tool for opserving local fleet of machines and reserving them for staging/testing.

---

## Deploy

Use this docker compose to deploy the system:

```yaml
version: "3.3"

services:
  opservatory:
    image: <put an actual deckerhub image here>
    ports:
     - "80:5000"
    volumes:
      - ./volumes:/app/opservatory/volumes
```

```bash
docker-compose up --build -d
```


## Update

```bash
docker-compose pull
docker-compose up --build -d
```