import os
import uuid
import datetime
from flask import Flask,request,jsonify,render_template
from embedder import embed
from pinecone_client import upsert_log,query_logs
from dotenv import load_dotenv

load_dotenv()

app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ingest',methods=['POST'])
def ingest():
    data=request.get_json()
    log_line=data.get('log')
    node=data.get('node','unknown')

    if not log_line:
        return jsonify({'error':'no log provided'}),400
    
    embedding=embed(log_line)
    log_id=str(uuid.uuid4())

    upsert_log(log_id,embedding,{
        'log':log_line,
        'node':node,
        'timestamp':datetime.datetime.utcnow().isoformat()
    })

    return jsonify({'status':'ok','id':log_id})

@app.route('/query',methods=['POST'])
def query():
    data=request.get_json()
    question=data.get('query')

    if not question:
        return jsonify({'error':'no question provided'}),400
    
    embedding=embed(question)
    results=query_logs(embedding,top_k=10)

    return jsonify({'results':[
        {
            'log': r['metadata']['log'],
            'node': r['metadata']['node'],
            'timestamp': r['metadata']['timestamp'],
            'score':round(r['score'],4)
        }
        for r in results
    ]})

if __name__=='__main__':
    app.run(debug=True,port=5001)