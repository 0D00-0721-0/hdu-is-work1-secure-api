# Work 1 - Secure REST API, Security CI, and Vulhub CVE Analysis

This project implements Work 1 of *Labs Full Manual HDU IS* (pages 1-5): a secure Python 3.12 + Flask + SQLite API, automated security checks, and an isolated Docker reproduction of Apache HTTP Server CVE-2021-41773.

**Verified outcome:** all 29 API tests and the live curl checks passed. GitHub Actions successfully ran tests, Bandit SAST, and pip-audit SCA. The vulnerable container disclosed its own `/etc/passwd`; the configuration mitigation blocked the same attack with HTTP 403 while the homepage remained available with HTTP 200. The separate version-upgrade proposal has **not** been dynamically verified because some image-layer downloads stalled.

## 1. Deliverables and evidence

- `app/` and `run.py`: secure API implementation.
- `requirements.txt`: pinned runtime dependencies with SHA-256 hashes.
- `requirements-dev.txt`: pinned testing/scanning tools and their dependencies.
- `.github/workflows/ci.yml`: CI for pushes, pull requests, and manual dispatch.
- `tests/test_api.py`: 29 authentication, input-validation, SQLi, XSS, authorization, and regression tests.
- `scripts/curl_tests.sh`: live HTTP checks using curl.
- `lab/vulnerable/`: upstream Vulhub Dockerfile and reproduction documentation.
- `fixes/`: verified configuration mitigation, an upgrade proposal, Compose files, and a patch.
- `evidence/`: actual execution logs, HTTP responses, and scanner reports.
- `screenshots/` and `docs/SCREENSHOTS.md`: screenshots and their evidence mapping.
- `docs/Work1_Report.md` and `docs/Work1_Report.pdf`: English report in the local submission package. Personal cover-page details are excluded from the public repository.

See the [verification record](evidence/VERIFICATION.md) and [submission links](docs/SUBMISSION.md). Clean scan results apply only to the documented scope and vulnerability data available at the time of scanning.

## 2. Installation and execution

Requirements: Python 3.12, pip, and Git. The CVE experiment also requires Docker Desktop and Docker Compose. Compose specifies `linux/amd64` for compatibility with the older upstream image on Apple Silicon.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-dev.txt
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python -m flask --app app:create_app init-db
python -m flask --app app:create_app create-user --login student
python run.py
```

User creation prompts for a dedicated lab password of at least 12 characters and at most 72 UTF-8 bytes. The database defaults to `instance/work1.sqlite3`, which Git ignores; `DATABASE_PATH` can override it. Waitress listens on `http://127.0.0.1:5001`. Flask debug mode is not enabled.

There is no hardcoded/default JWT signing secret. Keep `JWT_SECRET_KEY` private. Generating a different key invalidates older tokens; retain the same random key securely if tokens must survive a restart.

## 3. API endpoints

| Method | Path | Authentication | Input and successful response |
| --- | --- | --- | --- |
| POST | `/auth/login` | None | JSON `login` and `password`; JWT, Bearer scheme, and a 900-second lifetime |
| GET | `/api/data` | Bearer JWT | Current user's login name and private notes |
| POST | `/api/notes` | Bearer JWT | JSON `title` and `body`; creates an owned note and returns HTTP 201 |

```bash
# Use the dedicated password created for this lab.
curl --noproxy '*' -i http://127.0.0.1:5001/api/data
curl --noproxy '*' -sS http://127.0.0.1:5001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"student","password":"YOUR_LAB_PASSWORD"}'

# Enter the returned access_token without echoing it.
read -r -s TOKEN
curl --noproxy '*' -i http://127.0.0.1:5001/api/data \
  -H "Authorization: Bearer $TOKEN"
curl --noproxy '*' -i http://127.0.0.1:5001/api/notes \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Study plan","body":"Review JWT and parameterized SQL."}'
unset TOKEN
```

Run the complete live test script in another activated terminal. It does not print passwords or valid JWTs:

```bash
bash scripts/curl_tests.sh
# For a different account:
LAB_LOGIN=alice bash scripts/curl_tests.sh
```

Protected endpoints reject missing, forged, incorrectly signed, expired, or not-yet-valid tokens, incorrect issuer/audience values, missing required claims, and nonexistent users. Unknown accounts and wrong passwords receive the same 401 message. Malformed JSON returns 400, unsupported content types return 415, and oversized requests return 413.

## 4. Security controls

### SQL injection prevention

Queries involving user input or user identifiers use SQLite `?` placeholders:

```python
db.execute("SELECT id, password_hash FROM users WHERE login = ?", (name,))
db.execute("SELECT id, title, body FROM notes WHERE user_id = ? ORDER BY id", (g.user["id"],))
```

SQL syntax and data are handled separately. `' OR 1=1 --` remains a literal login value. SQL-looking note content is stored as text. `executescript` is used only for fixed schema statements in the source.

### XSS prevention

Original text is stored in SQLite. All returned user-controlled strings, including note titles, bodies, and login names, pass through `html.escape(..., quote=True)` at the response boundary. `<script>` becomes `&lt;script&gt;`. Creation and retrieval share the output function, avoiding double escaping in storage.

Responses use `application/json`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`, and a restrictive Content Security Policy. A future frontend should use `textContent` and context-appropriate encoding. HTML text escaping is not a general sanitizer for JavaScript, URL, or CSS contexts.

### Passwords, JWTs, and authorization

- bcrypt stores salted hashes at cost 12. A 72-byte limit prevents bcrypt input-length problems.
- An unknown account still causes one bcrypt check at the same cost, reducing a direct account-enumeration timing signal.
- JWT verification permits only `HS256` and checks the signature and required `exp`, `iat`, `nbf`, `sub`, `iss`, `aud`, and `jti` claims. Tokens expire after 15 minutes.
- Both business endpoints share an authentication decorator and verify that the subject user still exists.
- The authenticated user ID determines note ownership; clients cannot choose another owner in the request body.
- Startup rejects a missing signing key or one shorter than 32 bytes. Tokens contain no passwords/hashes. JWT signing does not encrypt the readable payload.

### Input constraints and scope

Requests are limited to 16 KiB. Titles must contain non-whitespace text and be at most 100 characters; bodies are limited to 2,000 characters. JSON shape, fields, and types are checked explicitly.

Production use would additionally require TLS, login rate limiting, key rotation, token revocation, auditing, and backups. A `jti` is issued, but this educational implementation has no revocation list.

## 5. CI: tests, SAST, and SCA

```bash
mkdir -p reports
python -m pytest -q --junitxml=reports/pytest.xml
bandit -r app run.py -f json -o reports/bandit.json
pip-audit -r requirements.txt --require-hashes -f json -o reports/pip-audit.json
```

Independent `tests`, `sast`, and `sca` matrix jobs fail when their checks fail, without cancelling the others. There is no `continue-on-error`. Reports are uploaded with `always()` and retained for 30 days. Permissions are limited to `contents: read`; Actions are pinned to verified SHAs, and dependencies use fixed versions and hashes.

Bandit scans `app/` and `run.py`, separately from the intentionally vulnerable material in `lab/`. It incorrectly flags the standard `token_type: Bearer` scheme label as a hardcoded password; only that line has a documented `# nosec B105` annotation. Other checks remain enabled.

pip-audit examines all 10 runtime dependencies in `requirements.txt`. It is the Python-specific SCA tool used here. The manual names OWASP Dependency-Check and Snyk as examples; an additional scan would be needed if the instructor requires one of those exact tools.

## 6. CVE selection and reproduction

The manual's suggested `vulhub/flask/CVE-2018-1000656` directory does not exist at the inspected revision. Its Flask directory contains only `ssti`, which must not be presented as that CVE. CVE-2018-1000656 concerns excessive memory consumption/DoS caused by JSON encoding handling in older Flask versions. Since another common service is permitted, this experiment uses the existing `httpd/CVE-2021-41773` environment.

Upstream: <https://github.com/vulhub/vulhub>. Inspected revision: `9b90d4276f84feed6333286afeb7e1250379a1da`. The upstream Dockerfile, README, and MIT license are retained. Local Compose replaces all-interface port 8080 with `127.0.0.1:18080`, adds resource limits and `no-new-privileges`, and mounts no sensitive host directories.

```bash
git clone --depth 1 https://github.com/vulhub/vulhub.git third_party/vulhub
# Compare the upstream README and Dockerfile in httpd/CVE-2021-41773.
docker compose -p work1-cve -f lab/vulnerable/compose.yml up --build -d
docker compose -p work1-cve -f lab/vulnerable/compose.yml ps
docker compose -p work1-cve -f lab/vulnerable/compose.yml exec -T apache httpd -v
bash scripts/verify_cve.sh vulnerable
```

Read-only request to the local container:

```bash
curl --noproxy '*' --path-as-is -i \
  'http://127.0.0.1:18080/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd'
```

`--path-as-is` prevents client-side path normalization. The container returned HTTP 200 and disclosed its own `/etc/passwd`; no host file was read. This verifies file disclosure, not RCE. Raw headers, status codes, and bodies are in `evidence/cve-vulnerable/`.

## 7. Root cause, verified mitigation, and upgrade proposal

Apache 2.4.49 incompletely normalized encoded parent-directory segments. Alias mapping through `/icons/` could lead outside the intended directory. Vulhub also changes root-directory access from `Require all denied` to `Require all granted`, allowing the escaped file to be read. CGI may permit command execution under additional conditions; this branch was not tested.

### Verified configuration mitigation

`fixes/Dockerfile.mitigation` uses the same 2.4.49 base image. It retains the autoindex Alias but keeps default denial for the filesystem root and does not enable CGI. Its loopback port is 18081:

```bash
docker compose -p work1-cve -f lab/vulnerable/compose.yml down
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml up --build -d
BASE_URL=http://127.0.0.1:18081 \
  bash scripts/verify_cve.sh fixed evidence/cve-mitigation
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml down
```

The **same attack path returned HTTP 403**, contained no account-file content, and the homepage returned HTTP 200 with `It works!`. Evidence is in `evidence/cve-mitigation/`. The control blocks this attack but does not remove the parser defect from the old binary; later permission changes could re-expose it.

### Version-upgrade proposal: not dynamically verified

The initial 2.4.50 fix was incomplete; the related bypass, CVE-2021-42013, was fixed in 2.4.51. The upgrade proposal in `fixes/Dockerfile` targets the inspected official 2.4.69 image and its default denial, CGI, and Alias settings.

```bash
docker compose -p work1-fixed -f fixes/compose.yml up --build -d
docker compose -p work1-fixed -f fixes/compose.yml exec -T apache httpd -v
bash scripts/verify_cve.sh fixed
docker compose -p work1-fixed -f fixes/compose.yml down
```

The 2.4.69 image and its Alpine variant were attempted, but some layer downloads stalled. **No successful upgraded container or upgrade-regression result is claimed.** The commands above are the follow-up procedure. The script requires the attack to return 400/403/404 without account-file content and the homepage to return 200.

Initial vulnerable-image downloads also encountered a DNS/IPv6 routing failure. A later attempt succeeded following a temporary DNS change and a user network switch; those overlapping changes do not establish a single cause of recovery. Wi-Fi DNS was restored to automatic configuration, and Docker proxy settings were not changed. Evidence-viewer screenshots are labelled as browser presentations of raw logs, not native terminal captures.

## 8. Git initialization and submission

The project has a local Git history and public remote. The ZIP excludes `.git`, local databases, passwords, and JWT secrets. To initialize a separate repository after extraction:

```bash
git init -b main
git add .
git commit -m "Complete Work 1 secure API and CVE verification"
gh auth status
# Only when creating a separate repository in your own account:
gh repo create work1-secure-api --public --source=. --remote=origin --push
gh run list --workflow ci.yml
```

The public repository contains code, technical documentation, and lab evidence. The report with personal cover-page details stays in the local package. Submit the report, ZIP, repository link, and successful CI link through the course platform. See `docs/SUBMISSION.md`.

## 9. References

1. *Labs Full Manual HDU IS*, Work 1, pages 1-5.
2. [Vulhub CVE-2021-41773](https://github.com/vulhub/vulhub/tree/9b90d4276f84feed6333286afeb7e1250379a1da/httpd/CVE-2021-41773).
3. [Apache security advisories](https://httpd.apache.org/security/vulnerabilities_24.html): CVE-2021-41773 and CVE-2021-42013.
4. [NVD: CVE-2021-41773](https://nvd.nist.gov/vuln/detail/CVE-2021-41773).
5. [Flask CVE-2018-1000656 advisory](https://github.com/advisories/GHSA-562c-5r94-xh97).
6. [Bandit](https://bandit.readthedocs.io/en/latest/) and [pip-audit](https://github.com/pypa/pip-audit).
7. [PyJWT](https://pyjwt.readthedocs.io/en/stable/usage.html) and [SQLite parameter binding](https://docs.python.org/3/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries).
