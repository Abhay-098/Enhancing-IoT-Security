from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, base64, json
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import symmetric
from cryptography.fernet import Fernet

DB = 'data.db'
CERT_DIR = 'certs'
os.makedirs(CERT_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS certs (name TEXT PRIMARY KEY, key TEXT, fingerprint TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, topic TEXT, mode TEXT, payload TEXT, wire TEXT, cert_used TEXT)''')
    conn.commit()
    conn.close()

init_db()

app = Flask(__name__)
CORS(app)

def now_ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/generate_cert', methods=['POST'])
def generate_cert():
    data = request.json or {}
    name = data.get('name') or 'device'
    # create a symmetric Fernet key to represent device key; store base64
    key = Fernet.generate_key()
    fingerprint = base64.urlsafe_b64encode(key)[:24].decode()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO certs (name,key,fingerprint,created_at) VALUES (?,?,?,?)', (name, key.decode(), fingerprint, now_ts()))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok','name':name,'fingerprint':fingerprint})

@app.route('/certs', methods=['GET'])
def list_certs():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT name,fingerprint,created_at FROM certs')
    rows = c.fetchall()
    conn.close()
    certs = [{'name':r[0],'fingerprint':r[1],'created_at':r[2]} for r in rows]
    return jsonify(certs)

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json or {}
    topic = data.get('topic','demo/topic')
    payload = data.get('payload','hello')
    mode = data.get('mode','insecure')
    cert_name = data.get('cert_name')
    wire = payload
    if mode == 'secure':
        # fetch key and encrypt payload using Fernet
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('SELECT key FROM certs WHERE name=?',(cert_name,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({'status':'error','error':'certificate not found'}),400
        key = row[0].encode()
        f = Fernet(key)
        wire = f.encrypt(payload.encode()).decode()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO messages (ts,topic,mode,payload,wire,cert_used) VALUES (?,?,?,?,?,?)', (now_ts(),topic,mode,payload,wire,cert_name))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

@app.route('/messages', methods=['GET'])
def get_messages():
    limit = int(request.args.get('limit', '100'))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id,ts,topic,mode,payload,wire,cert_used FROM messages ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    msgs = []
    for r in rows:
        msgs.append({'id':r[0],'ts':r[1],'topic':r[2],'mode':r[3],'payload':r[4],'wire':r[5],'cert_used':r[6]})
    return jsonify(msgs)

@app.route('/decrypt', methods=['POST'])
def decrypt_message():
    data = request.json or {}
    cert_name = data.get('cert_name')
    wire = data.get('wire')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT key FROM certs WHERE name=?',(cert_name,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'status':'error','error':'cert not found'}),400
    key = row[0].encode()
    f = Fernet(key)
    try:
        dec = f.decrypt(wire.encode()).decode()
        return jsonify({'status':'ok','payload':dec})
    except Exception as e:
        return jsonify({'status':'error','error':str(e)}),400

if __name__ == '__main__':
    # try to run with SSL if certs exist in CERT_DIR
    cert_path = os.path.join(CERT_DIR,'server.crt')
    key_path = os.path.join(CERT_DIR,'server.key')
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print('Starting server with HTTPS...')
        app.run(host='0.0.0.0', port=5000, ssl_context=(cert_path,key_path))
    else:
        print('Starting server WITHOUT TLS (HTTP). Generate certs/scripts/generate_server_cert.sh to enable TLS.')
        app.run(host='0.0.0.0', port=5000)
