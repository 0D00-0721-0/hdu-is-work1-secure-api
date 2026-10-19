#!/usr/bin/env bash
# Uses real HTTP; no JWT or password is printed. The server must already be running.
set -euo pipefail
BASE_URL="${BASE_URL:-http://127.0.0.1:5001}"
PYTHON="${PYTHON:-python3}"
: "${LAB_LOGIN:=student}"
if [[ -z "${LAB_PASSWORD:-}" ]]; then
  read -r -s -p 'Lab password: ' LAB_PASSWORD
  printf '\n'
fi
export LAB_LOGIN LAB_PASSWORD
tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
check() {
  local expected="$1" label="$2"; shift 2
  local actual
  actual=$(curl --noproxy '*' --silent --show-error --max-time 10 -o "$tmp_dir/response.json" -w '%{http_code}' "$@")
  [[ "$actual" == "$expected" ]] || { printf 'FAIL %s: expected %s, got %s\n' "$label" "$expected" "$actual"; cat "$tmp_dir/response.json"; exit 1; }
  printf 'PASS %-32s HTTP %s\n' "$label" "$actual"
}
check 401 no_token "$BASE_URL/api/data"
check 401 custom_endpoint_no_token -X POST "$BASE_URL/api/notes"
"$PYTHON" -c 'import json,os; print(json.dumps({"login":os.environ["LAB_LOGIN"],"password":os.environ["LAB_PASSWORD"]}))' > "$tmp_dir/login.json"
check 200 login -H 'Content-Type: application/json' --data-binary "@$tmp_dir/login.json" "$BASE_URL/auth/login"
"$PYTHON" -c 'import json,sys; print("Authorization: Bearer "+json.load(open(sys.argv[1]))["access_token"])' "$tmp_dir/response.json" > "$tmp_dir/auth-header"
check 200 protected_data -H "@$tmp_dir/auth-header" "$BASE_URL/api/data"
check 401 wrong_password -H 'Content-Type: application/json' -d '{"login":"student","password":"wrong"}' "$BASE_URL/auth/login"
check 401 sql_injection -H 'Content-Type: application/json' -d "{\"login\":\"' OR 1=1 --\",\"password\":\"anything\"}" "$BASE_URL/auth/login"
check 401 forged_token -H 'Authorization: Bearer invalid.jwt.token' "$BASE_URL/api/data"
check 201 xss_payload -H "@$tmp_dir/auth-header" -H 'Content-Type: application/json' -d '{"title":"<script>alert(1)</script>","body":"<img src=x onerror=alert(1)>"}' "$BASE_URL/api/notes"
"$PYTHON" -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "&lt;script&gt;" in d["title"] and "<img" not in d["body"]; print("PASS output_escaping",d)' "$tmp_dir/response.json"
check 200 read_after_write -H "@$tmp_dir/auth-header" "$BASE_URL/api/data"
printf 'All live curl checks passed.\n'
