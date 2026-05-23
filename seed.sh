BASE="http://localhost:5001/ingest"

ingest() {
  curl -s -X POST $BASE \
    -H "Content-Type: application/json" \
    -d "{\"log\": \"$1\", \"node\": \"$2\"}" > /dev/null
  echo "ingested: $1"
}

# WAL replays
ingest "WAL replayed 84 entries from /data/wal_node1:6000.log" "node1:6000"
ingest "WAL replayed 61 entries from /data/wal_node2:6001.log" "node2:6001"
ingest "WAL replayed 0 entries from /data/wal_node3:6002.log" "node3:6002"

# Node failures
ingest "Node unavailable: node2:6001" "node1:6000"
ingest "Node unavailable: node2:6001" "node3:6002"
ingest "Node unavailable: node3:6002" "node1:6000"
ingest "Node unavailable: node3:6002" "node2:6001"

# Recoveries
ingest "Node recovered: node2:6001" "node1:6000"
ingest "Node recovered: node2:6001" "node3:6002"
ingest "Node recovered: node3:6002" "node1:6000"
ingest "Node recovered: node3:6002" "node2:6001"

# High load
ingest "processed_requests_ size: 156" "node1:6000"
ingest "processed_requests_ size: 243" "node2:6001"
ingest "processed_requests_ size: 89"  "node3:6002"

# Replication
ingest "replicas for key user1: node2:6001 node3:6002 node1:6000" "node1:6000"
ingest "replicas for key session_abc: node1:6000 node3:6002 node2:6001" "node2:6001"
ingest "replicas for key order_99: node3:6002 node1:6000 node2:6001" "node3:6002"

echo "done — all logs seeded"