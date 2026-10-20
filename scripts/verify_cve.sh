#!/usr/bin/env bash
# Local-only Ghostcat (CVE-2020-1938) checks.
set -euo pipefail
phase="${1:?Usage: verify_cve.sh vulnerable|fixed [output-directory]}"
[[ "$phase" == vulnerable || "$phase" == fixed ]] || exit 2
out="${2:-evidence/cve-$phase}"
mkdir -p "$out"
base="${BASE_URL:-http://127.0.0.1:18080}"
ajp_port="${AJP_PORT:-18009}"
[[ "$base" =~ ^http://127\.0\.0\.1:[0-9]+$ ]] || { echo 'Only loopback lab URLs are allowed'; exit 2; }
http_port="${base##*:}"

curl_args=(--noproxy '*' --silent --show-error --max-time 10)
curl "${curl_args[@]}" -D "$out/homepage.headers" -o "$out/homepage.body" \
  -w '%{http_code}' "$base/" > "$out/homepage.status"
printf '%-12s HTTP %s\n' homepage "$(cat "$out/homepage.status")"
[[ "$(cat "$out/homepage.status")" == 200 ]]
grep -qi 'Apache Tomcat' "$out/homepage.body"

set +e
python3 scripts/ghostcat_read.py --port "$ajp_port" --server-port "$http_port" \
  --file /WEB-INF/web.xml > "$out/ajp.body" 2> "$out/ajp.err"
ajp_rc=$?
set -e

if [[ $ajp_rc -eq 0 ]] && grep -q '<web-app' "$out/ajp.body"; then
  echo 200 > "$out/ajp.status"
  printf '%-12s HTTP %s (web.xml disclosed)\n' ajp "$(cat "$out/ajp.status")"
  if [[ "$phase" == vulnerable ]]; then
    printf 'PASS: vulnerable AJP connector returned /WEB-INF/web.xml.\n'
  else
    echo 'FAIL: the AJP file read still succeeds' >&2
    exit 1
  fi
else
  echo refused > "$out/ajp.status"
  printf '%-12s %s\n' ajp "$(cat "$out/ajp.status")"
  if [[ "$phase" == vulnerable ]]; then
    echo 'FAIL: expected the AJP file read to succeed' >&2
    exit 1
  fi
  ! grep -q '<web-app' "$out/ajp.body"
  printf 'PASS: the AJP request is blocked; homepage still works.\n'
fi

{
  echo "status: $(cat "$out/ajp.status")"
  if [[ -s "$out/ajp.err" ]]; then
    echo "stderr:"
    cat "$out/ajp.err"
  fi
} > "$out/ajp.outcome.txt"
