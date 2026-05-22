import subprocess
import requests
import threading 
import re
import sys

NODES=[
    {"name":"constella-node1","id":"node1:6000"},
    {"name":"constella-node2","id":"node2:6001"},
    {"name":"constella-node3","id":"node3:6002"},
]

INGEST_URL="http://localhost:5001/ingest"

SKIP_PATTERNS = [
    r"^\s*$",                    # empty lines
    r"replicas for:",            # too frequent, low signal
    r"get_replicas returning",   # debug output
    r"GET replicas for key",     # debug output
    r"GET key=",                 # debug output
    r"Ring size after adding",   # startup noise
]

def should_ingest(line:str)->bool:
    for pattern in SKIP_PATTERNS:
        if re.search(pattern,line):
            return False
    return True

def tail_node(node:dict):
    print(f"[collector] tailing {node['name']}...")
    proc=subprocess.Popen(
        ["docker","logs","-f","--tail","0",node["name"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    for line in proc.stdout:
        line=line.strip()
        if not line or not should_ingest(line):
            continue
        try:
            resp=requests.post(INGEST_URL,json={
                "log":line,
                "node":node["id"]
            },timeout=5)
            print(f"[{node['id']}] ingested: {line[:60]}")
        except Exception as e:
            print(f"[{node['id']}] ingest error: {e}")

def main():
    threads=[]
    for node in NODES:
        t=threading.Thread(target=tail_node,args=(node,),daemon=True)
        t.start()
        threads.append(t)
    print("[collector] watching all nodes.")
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[collector] stopped")
        sys.exit(0)

if __name__=="__main__":
    main()