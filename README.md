# AssistKB Search

## Tester l'API

```bash
uvicorn app.api:app --reload --port 8000
```

et dans un autre terminal :

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la capitale de l’Australie ?"}'
```