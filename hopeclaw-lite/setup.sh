#!/usr/bin/env bash
# HopeClaw Lite — webhook setup for Oracle Cloud VM
set -euo pipefail

# ── detect public IP ──────────────────────────────────────────────────────────
PUBLIC_IP=$(curl -s --max-time 5 https://api.ipify.org || hostname -I | awk '{print $1}')
echo "Public IP: $PUBLIC_IP"

# ── generate self-signed cert (Telegram accepts these) ───────────────────────
if [[ ! -f cert.pem ]]; then
  openssl req -newkey rsa:2048 -sha256 -nodes -keyout key.pem \
    -x509 -days 3650 -out cert.pem \
    -subj "/CN=$PUBLIC_IP"
  echo "Certificate generated."
fi

# ── open firewall port (Oracle Cloud) ────────────────────────────────────────
if command -v iptables &>/dev/null; then
  iptables -I INPUT -p tcp --dport 8443 -j ACCEPT 2>/dev/null || true
fi

# ── export env and launch ─────────────────────────────────────────────────────
export WEBHOOK_URL="https://$PUBLIC_IP:8443"
export WEBHOOK_PORT=8443
export WEBHOOK_CERT=cert.pem
export WEBHOOK_KEY=key.pem

echo "Starting HopeClaw Lite in webhook mode..."
echo "Webhook URL: $WEBHOOK_URL/webhook"
python3 app.py
