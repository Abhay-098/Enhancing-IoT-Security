Full-stack Server-Client Secure vs Insecure Demo
================================================

Contents:
- backend/server.py  -> Flask REST API with SQLite persistence. Can run with TLS (HTTPS).
- frontend/streamlit_app.py -> Streamlit UI that polls the backend for messages and can send messages.
- scripts/generate_server_cert.sh -> OpenSSL script to generate a self-signed server certificate (for HTTPS).
- requirements.txt -> Python dependencies.

Quick start (local testing):
1. Create Python env and install dependencies:
   pip install -r requirements.txt
2. Generate a server certificate (for HTTPS) - optional for local plain HTTP testing:
   chmod +x scripts/generate_server_cert.sh
   ./scripts/generate_server_cert.sh certs
   This creates certs/server.crt and certs/server.key
3. Start the backend server:
   # uses HTTPS if certs present, otherwise HTTP
   python backend/server.py
   By default server runs on 0.0.0.0:5000
4. Start the Streamlit frontend (in a separate terminal):
   streamlit run frontend/streamlit_app.py --server.port 8501
5. Open http://localhost:8501 and try Sender and Receiver across multiple browser windows.

Notes about real hosting:
- To allow multiple remote users, deploy the backend to a hosting provider (e.g., Render, DigitalOcean, or a VM) and ensure port 5000 is open and TLS certs installed.
- Streamlit can be deployed on Streamlit Cloud, but for cross-origin calls to your backend you must enable CORS and host the backend on a public HTTPS endpoint.

Security notes:
- This demo uses HTTPS (TLS) for transport when certs are present. It also supports 'secure' payload option where the server will encrypt the payload before saving using a symmetric key derived per certificate (simulated).
- For real production MQTT/TLS integration, a full broker (Mosquitto) with proper certs and client authentication is recommended.
