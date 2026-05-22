# Constella Lens

Constella Lens is a semantic log intelligence tool for [Constella](https://github.com/arpan6103/constella) — a distributed key-value store. It ingests real-time logs from all cluster nodes, embeds them using a local sentence transformer model, stores them in Pinecone, and lets you query across your entire distributed system in natural language.

---

## What it does

Instead of grepping log files or scrolling through Docker output, you ask questions:

```
which node went down?
show me WAL replay events
which node had high request volume?
when did node2 recover?
show me all replication events
```

And get back semantically ranked results with node attribution, timestamps, and relevance scores.

---

## Architecture

```text
┌─────────────────────────────────────────────┐
│              Constella Cluster               │
│  node1:6000   node2:6001   node3:6002        │
└────────────────────┬────────────────────────┘
                     │ docker logs -f
                     ▼
              ┌─────────────┐
              │ collector.py │  tails all 3 nodes in real time
              └──────┬──────┘
                     │ POST /ingest
                     ▼
              ┌─────────────┐
              │   app.py    │  Flask API
              └──────┬──────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   embedder.py            pinecone_client.py
   sentence-transformers   Pinecone vector index
   all-MiniLM-L6-v2        384-dim cosine search
          │                     │
          └──────────┬──────────┘
                     ▼
              ┌─────────────┐
              │  index.html  │  Search UI
              └─────────────┘
```

---

## Stack

| Component | Technology |
|-----------|------------|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (local, no API cost) |
| Vector store | Pinecone (serverless, free tier) |
| API | Flask |
| Log collection | Python subprocess + Docker logs |
| Frontend | Vanilla HTML/CSS/JS |

---

## Project Structure

```text
constella-lens/
├── app.py              # Flask API — /ingest, /query, /stats
├── collector.py        # Real-time Docker log tailer
├── embedder.py         # sentence-transformers wrapper
├── pinecone_client.py  # Pinecone upsert and query
├── templates/
│   └── index.html      # Search UI
├── .env                # API keys (not committed)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/constella-lens
cd constella-lens
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
PINECONE_API_KEY=your_key_here
PINECONE_INDEX=constella-logs
```

Get your Pinecone API key at [pinecone.io](https://pinecone.io).

### 3. Start Constella

```bash
cd ../constella
docker compose up --build
```

### 4. Start Constella Lens

```bash
# terminal 1 — API
python3 app.py

# terminal 2 — collector
python3 collector.py
```

### 5. Open the UI

```
http://localhost:5001
```

---

## API

### `POST /ingest`

Ingest a log line into the vector index.

```json
{
  "log": "Node unavailable: node2:6001",
  "node": "node1:6000"
}
```

Response:
```json
{
  "status": "ok",
  "id": "9f33dc7c-ae28-46a3-9aa4-082a745209e2"
}
```

### `POST /query`

Query logs in natural language.

```json
{
  "query": "which node went down?"
}
```

Response:
```json
{
  "results": [
    {
      "log": "Node unavailable: node2:6001",
      "node": "node1:6000",
      "timestamp": "2026-05-22T13:09:24.608202",
      "score": 0.6341
    }
  ]
}
```

### `GET /stats`

Returns total vectors indexed.

```json
{
  "total_vectors": 42
}
```

---

## How the collector works

`collector.py` tails all 3 Constella Docker containers simultaneously using `docker logs -f`. Each log line is filtered against a skip list to remove noise (debug output, zero-value metrics, frequent heartbeat logs). Meaningful events — node failures, recoveries, WAL replays, high request volume — are embedded and ingested in real time.

```python
SKIP_PATTERNS = [
    r"replicas for:",          # too frequent
    r"get_replicas returning", # debug
    r"Ring size after adding", # startup noise
    r"processed_requests_ size: 0",  # zero is noise
]
```

High-volume metrics like `processed_requests_` are only ingested when count exceeds 10, filtering idle heartbeat noise while preserving genuine load signals.

---

## Example queries

| Query | What it finds |
|-------|---------------|
| `which node went down?` | Node unavailable events |
| `show me node recovery events` | Node recovered events |
| `WAL replay on startup` | WAL replay log lines |
| `high request processing volume` | processed_requests > 10 |
| `replica assignment for keys` | Replication routing logs |
| `node started listening` | Startup events |

---

## Concepts demonstrated

- **Semantic search** — natural language queries over structured system logs
- **Vector embeddings** — sentence-transformers converting log text to 384-dim vectors
- **Cosine similarity** — ranking results by semantic relevance, not keyword match
- **Real-time ingestion** — streaming Docker logs into a vector index as events occur
- **Observability** — turning raw distributed system logs into queryable intelligence

---

## Related

Built as a companion tool to [Constella](https://github.com/YOUR_USERNAME/constella) — a distributed key-value store with consistent hashing, quorum replication, WAL persistence, and heartbeat failure detection.