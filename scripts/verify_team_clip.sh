#!/usr/bin/env zsh
set -euo pipefail

# Base URL can be overridden: BASE_URL=http://localhost:5000 zsh scripts/verify_team_clip.sh
BASE_URL=${BASE_URL:-http://127.0.0.1:5000}

echo "Preflight health check on $BASE_URL ..."
if ! curl -fsS -m 3 "$BASE_URL/api/v1/health" >/dev/null; then
  echo "Backend not reachable at $BASE_URL. Please start the Flask server and retry." >&2
  echo "Example: FLASK_APP=app.py FLASK_ENV=development flask run" >&2
  exit 7
fi

U="cliptest_${RANDOM}${RANDOM}"; P="pass1234"
printf '{"username":"%s","password":"%s"}\n' "$U" "$P" > /tmp/reg.json

echo "Registering: $U"
curl -fsS -X POST "$BASE_URL/api/v1/auth/register" \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/reg.json | jq -C '.code,.msg,.data'

echo "Logging in..."
TOKEN=$(curl -fsS -X POST "$BASE_URL/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/reg.json | jq -r '.data.access_token // empty')
if [[ -z "$TOKEN" ]]; then echo "Login failed" >&2; exit 1; fi
echo "TOKEN_PREFIX=${TOKEN:0:20}..."

echo "Health before load:"
curl -fsS "$BASE_URL/api/v1/health" | jq '{embedding_backend_config, embedding_backend_loaded, embedding_dim}'

echo "Triggering text search..."
curl -fsS -X POST "$BASE_URL/api/v1/search/text" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"query":"hello","k":1}' | jq '{code,msg,data}'

sleep 1
echo "Health after load:"
curl -fsS "$BASE_URL/api/v1/health" | jq '{embedding_backend_config, embedding_backend_loaded, embedding_dim}'

echo "Done."
