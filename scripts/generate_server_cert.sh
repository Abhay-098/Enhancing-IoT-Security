#!/usr/bin/env bash
# Usage: ./generate_server_cert.sh outdir
OUT=${1:-certs}
mkdir -p "$OUT"
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout "$OUT/server.key" -out "$OUT/server.crt" -subj "/C=IN/ST=State/L=City/O=Demo/OU=Backend/CN=localhost"
echo "Generated certs in $OUT: server.crt and server.key"
