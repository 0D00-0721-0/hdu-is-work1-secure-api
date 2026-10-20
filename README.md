# Work 1 - Secure REST API, Security CI, and Vulhub CVE Analysis

This project implements Work 1 of *Labs Full Manual HDU IS* (pages 1-5): a secure Python 3.12 + Flask + SQLite API, automated security checks, and an isolated Docker reproduction of Apache Tomcat CVE-2020-1938 (Ghostcat).

**Verified outcome:** all 29 API tests and the live curl checks passed. GitHub Actions successfully ran tests, Bandit SAST, and pip-audit SCA. The vulnerable Tomcat 9.0.30 container returned `/WEB-INF/web.xml` over AJP without a secret; removing the AJP connector and upgrading to Tomcat 9.0.31 both blocked the same request while the HTTP homepage returned 200.

## 1. Deliverables and evidence

- `app/` and `run.py`: secure API implementation.
- `requirements.txt`: pinned runtime dependencies with SHA-256 hashes.
- `requirements-dev.txt`: pinned testing/scanning tools and their dependencies.
- `.github/workflows/ci.yml`: CI for pushes, pull requests, and manual dispatch.
- `tests/test_api.py`: 29 authentication, input-validation, SQLi, XSS, authorization, and regression tests.
- `scripts/curl_tests.sh`: live HTTP checks using curl.
- `lab/vulnerable/`: upstream Vulhub Compose file and README for Tomcat 9.0.30.
- `fixes/`: verified AJP-disable mitigation, verified Tomcat 9.0.31 upgrade, Compose files, and explanatory documentation.
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

The experiment uses Vulhub's `tomcat/CVE-2020-1938` environment: Apache Tomcat 9.0.30 with the AJP 1.3 connector on port 8009. Ghostcat is an AJP file read/include flaw; the manual permits a suitable Vulhub service, and Tomcat is a widely deployed Java middleware.

Upstream: <https://github.com/vulhub/vulhub>. Inspected revision: `9b90d4276f84feed6333286afeb7e1250379a1da`. The upstream README and license are retained. Local Compose restricts HTTP and AJP to loopback (`127.0.0.1:18080`, `127.0.0.1:18009`), adds resource limits and `no-new-privileges`, and mounts no host directories.

```bash
git clone --depth 1 https://github.com/vulhub/vulhub.git third_party/vulhub
# Compare the upstream README in tomcat/CVE-2020-1938.
docker compose -p work1-cve -f lab/vulnerable/compose.yml up -d
docker compose -p work1-cve -f lab/vulnerable/compose.yml exec -T tomcat \
  sh -c 'java -cp $CATALINA_HOME/lib/catalina.jar org.apache.catalina.util.ServerInfo | head -1'
BASE_URL=http://127.0.0.1:18080 AJP_PORT=18009 \
  bash scripts/verify_cve.sh vulnerable evidence/cve-vulnerable
```

The read-only AJP probe:

```bash
python3 scripts/ghostcat_read.py --port 18009 --server-port 18080 \
  --file /WEB-INF/web.xml
```

The HTTP homepage returned 200. The AJP request returned 200 and the body contained the complete `/WEB-INF/web.xml` (1,227 bytes, including `<web-app>`). This verifies file read, not code execution. Raw responses are in `evidence/cve-vulnerable/`.

## 7. Root cause, verified mitigation, and verified upgrade

Tomcat's AJP13 connector accepts a `ForwardRequest` from any client that can reach port 8009. The request can carry `javax.servlet.include.request_uri` and `javax.servlet.include.servlet_path` attributes. In 9.0.30 and earlier, the connector requires no shared secret by default. The AJP processor uses the include attributes when dispatching to the default servlet, so the servlet reads a client-chosen path instead of the requested URI.

The result is a file read below the web application, for example `/WEB-INF/web.xml` or source files. If the application has a file-upload feature, the same mechanism can include an uploaded JSP file; that is the code-execution path described by the Ghostcat advisory. The defect is in AJP request handling, not in the HTTP endpoints.

### Verified configuration mitigation

`fixes/Dockerfile.mitigation` keeps the 9.0.30 image but removes the AJP connector from `conf/server.xml`. The HTTP homepage is still served on loopback port 18081; AJP is not published.

```bash
docker compose -p work1-cve -f lab/vulnerable/compose.yml down
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml up --build -d
BASE_URL=http://127.0.0.1:18081 AJP_PORT=18019 \
  bash scripts/verify_cve.sh fixed evidence/cve-mitigation
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml down
```

The AJP request was refused, no file content was returned, and the homepage returned 200. Evidence is in `evidence/cve-mitigation/`. The mitigation removes the attack surface but leaves the old 9.0.30 binary in place.

### Verified version upgrade

Tomcat 9.0.31 is the first 9.0.x release with the CVE-2020-1938 fix. The official image does not enable AJP by default; `fixes/Dockerfile` also restores the default web applications for the homepage check.

```bash
docker compose -p work1-fixed -f fixes/compose.yml up --build -d
docker compose -p work1-fixed -f fixes/compose.yml exec -T tomcat \
  sh -c 'java -cp $CATALINA_HOME/lib/catalina.jar org.apache.catalina.util.ServerInfo | head -1'
BASE_URL=http://127.0.0.1:18082 AJP_PORT=18029 \
  bash scripts/verify_cve.sh fixed evidence/cve-fixed
docker compose -p work1-fixed -f fixes/compose.yml down
```

The container reported Apache Tomcat/9.0.31. The AJP request was refused and returned no file content; the homepage returned 200. Evidence is in `evidence/cve-fixed/`. A deployment that needs AJP should bind it to a trusted interface, set `secretRequired="true"` with a strong secret, and firewall port 8009.

Evidence-viewer screenshots are browser presentations of raw logs, not native terminal captures.

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
2. [Vulhub CVE-2020-1938](https://github.com/vulhub/vulhub/tree/9b90d4276f84feed6333286afeb7e1250379a1da/tomcat/CVE-2020-1938).
3. [NVD: CVE-2020-1938](https://nvd.nist.gov/vuln/detail/CVE-2020-1938).
4. [Snyk: Ghostcat](https://snyk.io/blog/ghostcat-breach-affects-all-tomcat-versions/).
5. [Apache Tomcat 9 security page](https://tomcat.apache.org/security-9.html).
6. [Apache Tomcat AJP connector documentation](https://tomcat.apache.org/tomcat-9.0-doc/config/ajp.html).
7. [Bandit](https://bandit.readthedocs.io/en/latest/) and [pip-audit](https://github.com/pypa/pip-audit).
8. [PyJWT](https://pyjwt.readthedocs.io/en/stable/usage.html) and [SQLite parameter binding](https://docs.python.org/3/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries).
