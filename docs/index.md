# Quickstart

!!! warning inline end
    TODO: push docker container to docker hub

To launch opservatory server, deploy it using docker container:

```
docker --name opservatory -v ${PWD}/opservatory:/app/opservatory/mounts -p 80:5000 <DOCKER HUB CONTAINER>
```

or use docker-compose with `docker-compose.yml` containing the following configuration:

```yaml
version: "3.3"

services:
  opservatory:
    image: <DOCKER HUB IMAGE>
    ports:
     - "80:5000"
    volumes:
      - ./opservatory:/app/opservatory/mounts

```

and run 

```
docker-compose up -d
```

Then you can go and see your Opservatory instance running at <http://localhost>
