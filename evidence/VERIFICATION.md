# Recorded Verification Results

Experiment date: 19-20 October 2026 (Asia/Shanghai).

| Item | Recorded result | Original evidence |
| --- | --- | --- |
| API tests | 29 passed | `pytest.txt`, `pytest.xml` |
| Live HTTP curl checks | All passed | `curl-tests.txt` |
| SAST | No unhandled Bandit findings; one Bearer-label false positive has a line-specific B105 annotation | `bandit.json`, `bandit-console.txt` |
| SCA | 10 runtime dependencies; no known vulnerabilities | `pip-audit.json`, `pip-audit-console.txt` |
| Docker | Engine 29.8.2, Desktop 4.95.0, Compose 5.6.0 | Build and container logs |
| Vulnerable environment | Tomcat 9.0.30; homepage 200; AJP 200; `/WEB-INF/web.xml` disclosed | `cve-vulnerable-*`, `cve-vulnerable/` |
| Configuration mitigation | Tomcat 9.0.30 with AJP disabled; AJP refused; homepage 200 | `cve-mitigation-*`, `cve-mitigation/` |
| Version upgrade | Tomcat 9.0.31; AJP refused; homepage 200 | `cve-fixed-*`, `cve-fixed/` |
| GitHub Actions | tests, SAST, and SCA succeeded in run 39196313211 (downloaded reports) and in the latest run 39366086767 (commit c3553cb) | `ci-current/`, `docs/SUBMISSION.md` |

Tomcat image pulls: the first `vulhub/tomcat:9.0.30` pull timed out on one layer; a retry completed it, and the recorded runs use the completed image. The AJP probe is a read-only request for `/WEB-INF/web.xml`; it does not write or execute anything.

Clean Bandit/SCA results are limited to the stated scopes, rules, vulnerability data, and recorded time. They do not establish the absence of all security risks. The documentation and evidence-viewer headings have been translated into English; original execution outputs remain unchanged.
