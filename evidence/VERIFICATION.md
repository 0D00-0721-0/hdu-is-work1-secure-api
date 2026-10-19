# Recorded Verification Results

Experiment date: 19 October 2026 (Asia/Shanghai).

| Item | Recorded result | Original evidence |
| --- | --- | --- |
| API tests | 29 passed | `pytest.txt`, `pytest.xml` |
| Live HTTP curl checks | All passed | `curl-tests.txt` |
| SAST | No unhandled Bandit findings; one Bearer-label false positive has a line-specific B105 annotation | `bandit.json`, `bandit-console.txt` |
| SCA | 10 runtime dependencies; no known vulnerabilities | `pip-audit.json`, `pip-audit-console.txt` |
| Docker | Engine 29.8.2, Desktop 4.95.0, Compose 5.6.0 | Build and container logs |
| Vulnerable environment | Apache 2.4.49; homepage 200; traversal 200; container `/etc/passwd` disclosed | `cve-vulnerable-*`, `cve-vulnerable/` |
| Configuration mitigation | Binary still 2.4.49; same traversal path 403; homepage 200 | `cve-mitigation-*`, `cve-mitigation/` |
| Upgrade proposal | Metadata for 2.4.69 and the Alpine variant was accessible, but some layer downloads stalled; no dynamic upgrade verification | `docker-fixed-build.txt`, `docker-upgrade-download.txt` |
| GitHub Actions | tests, SAST, and SCA succeeded in run 39196313211; final implementation/submission run 39196644394 also succeeded | `ci-current/`, `docs/SUBMISSION.md` |

Initial network failure: Docker attempted to download image layers through a hostname resolving to unreachable IPv6, producing `no route to host`. A later vulnerable-image download succeeded after a temporary DNS adjustment and a user network switch. These overlapping changes do not prove a single cause of recovery. Wi-Fi DNS was restored to its original automatic configuration, and Docker proxy settings were not modified.

Clean Bandit/SCA results are limited to the stated scopes, rules, vulnerability data, and recorded time. They do not establish the absence of all security risks. The documentation and evidence-viewer headings have been translated into English; original execution outputs remain unchanged.
