# Screenshot Checklist and Evidence Mapping

Every screenshot must correspond to the project's actual evidence. Original logs are the primary records. Upstream README images are not used as substitutes for this experiment's results.

| ID | Content | Original evidence | Supplied image |
| --- | --- | --- | --- |
| S01 | Live curl checks: unauthenticated 401, login 200, creation 201, SQLi/JWT rejection | `evidence/curl-tests.txt` | `S01-S04-api-evidence.png` |
| S02 | pytest: 29 passed | `evidence/pytest.txt`, `evidence/pytest.xml` | `S01-S04-api-evidence.png` |
| S03 | Bandit: no unhandled findings, with scope and metrics | `evidence/bandit.json` | `S01-S04-api-evidence.png` |
| S04 | pip-audit: 10 runtime dependencies, no known vulnerabilities | `evidence/pip-audit.json` | `S01-S04-api-evidence.png` |
| S05 | Successful tests/SAST/SCA jobs and the workflow run | `docs/SUBMISSION.md`, `evidence/ci-current/` | `S05-actions-success.png`: native GitHub Actions page |
| S06 | Apache 2.4.49 and the traversal response disclosing a container file | `evidence/cve-vulnerable-version.txt`, `evidence/cve-vulnerable/` | `S06-S07-cve-evidence.png` |
| S07 | Configuration mitigation: attack 403 and homepage 200; binary still 2.4.49 | `evidence/cve-mitigation-version.txt`, `evidence/cve-mitigation/` | `S06-S07-cve-evidence.png` |
| S08 | Configuration/upgrade files and the upgrade diff | `fixes/httpd.patch`, `fixes/README.md` | Supplied as reviewable files |
| S09 | Verified upgrade: Apache 2.4.69, attack 400, homepage 200; permissive-config cross-check also 400 with `/icons/` 200 | `evidence/cve-fixed-*`, `evidence/cve-fixed/`, `evidence/cve-fixed-permissive-*`, `evidence/cve-fixed-permissive/` | Rendered in `docs/evidence-cve.html` and `S06-S07-cve-evidence.png` |

The S01-S04 and S06-S07 images are **browser presentations of saved raw logs**, with English headings and source hashes. They are not native terminal screenshots or native Actions report pages. Recreating those evidence pages in English does not rerun or alter the original tests. S05 is a genuine GitHub Actions page capture.

Do not expose passwords, valid JWTs, or signing keys in additional screenshots. Keep relevant commands, response codes, versions, run links, and timestamps visible.
