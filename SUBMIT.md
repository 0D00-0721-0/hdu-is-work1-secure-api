# Work 1 Submission Guide

Public repository: https://github.com/0D00-0721-0/hdu-is-work1-secure-api

Latest successful implementation/submission CI (commit c3553cb): https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39366086767

| Submission item | Location |
| --- | --- |
| Project overview, API usage, security controls, and CVE procedure | `README.md` |
| English laboratory report | `docs/Work1_Report.pdf`; editable source: `docs/Work1_Report.md`, in the local package only |
| API implementation and pinned dependencies | `app/`, `run.py`, `requirements*.txt` |
| Automated push/PR security CI | `.github/workflows/ci.yml` |
| Live curl checks and automated tests | `scripts/curl_tests.sh`, `tests/test_api.py` |
| Vulnerable environment and upstream provenance | `lab/` |
| Verified configuration mitigation and verified Tomcat 9.0.31 upgrade | `fixes/` |
| Original execution evidence and CI reports | `evidence/` |
| Screenshots and evidence mapping | `screenshots/`, `docs/SCREENSHOTS.md` |

Completed and recorded: 29 automated tests, live HTTP checks, Bandit SAST, pip-audit SCA, successful GitHub Actions runs, Docker/Vulhub AJP file-read reproduction, a configuration mitigation that removes the AJP connector while retaining a working homepage, and a verified Tomcat 9.0.31 upgrade that also blocks the AJP request with the homepage still available.

Both protection measures are verified: the mitigation keeps the 9.0.30 binary but removes the AJP connector, and the upgrade uses Tomcat 9.0.31. A deployment that needs AJP should require a secret and restrict port 8009.

The report already contains the student's name and HDU ID, and the variant number is CVE-2020-1938. Submit the English report and ZIP through the course platform with the repository and successful CI links. The report is excluded from the public repository because it contains personal cover-page details.

The Chinese submission ZIP from the earlier draft is retained as a backup. Use `Work1_Submission_23320321_EN.zip` for the English submission.
