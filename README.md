![](docs/brands/full_logo_white.svg#gh-dark-mode-only)
![](docs/brands/full_logo_white.svg#gh-light-mode-only)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version">
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

API for checking docker containers states in a small infrastructure

---

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

Made by [Subatiq](https://github.com/subatiq) for the team of Edge Vision. Powered by [Kornet](https://subatiq.github.io/kornet/)
