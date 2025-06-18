# LarngearLM-Backend

Backend that running LLM with backend server. That will connect to Frontend website. Call the API from frontend and this Backend will connect to LLM to do summarize pdf, YouTube link, etc... into paragraph or whatsoever.

I worked at Larngear Technology company and I just happen to name it like the company's name. Nothing special, This repository doesn't relate to Chula, Probably company doesn't even have a name for this. I just name it by myself because I don't know what to call it.

## How to start

```bash
docker compose up -d
```

```bash
# manually pull llama3.1 model at the first time
docker exec larngearlm-backend-ollama-1 ollama pull llama3.1:latest
```

```bash
# manually create virtual environment at the first time
pip -m venv .venv
pip install -r requirements.txt
```

```bash
uvicorn app.main:app --reload
```

## API docs

API docs from FastAPI

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## TL;DR

It's NotebookLM clone. NotebookLM is one of Google's product.
