# Work 1 Submission Guide

Public repository: https://github.com/0D00-0721-0/hdu-is-work1-secure-api

Verified successful implementation/submission CI: https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39196644394

| Submission item | Location |
| --- | --- |
| Project overview, API usage, security controls, and CVE procedure | `README.md` |
| English laboratory report | `docs/Work1_Report.pdf`; editable source: `docs/Work1_Report.md`, in the local package only |
| API implementation and pinned dependencies | `app/`, `run.py`, `requirements*.txt` |
| Automated push/PR security CI | `.github/workflows/ci.yml` |
| Live curl checks and automated tests | `scripts/curl_tests.sh`, `tests/test_api.py` |
| Vulnerable environment and upstream provenance | `lab/` |
| Verified configuration mitigation and unverified upgrade proposal | `fixes/` |
| Original execution evidence and CI reports | `evidence/` |
| Screenshots and evidence mapping | `screenshots/`, `docs/SCREENSHOTS.md` |

Completed and recorded: 29 automated tests, live HTTP checks, Bandit SAST, pip-audit SCA, successful GitHub Actions runs, Docker/Vulhub file-disclosure reproduction, and configuration mitigation that returned 403 for the same attack while retaining a working homepage.

Limitation: some layers of the newer Apache images could not be downloaded successfully. The version-upgrade proposal has not been dynamically verified. The verified protection is `Dockerfile.mitigation` with `compose.mitigation.yml`. It still uses the 2.4.49 binary; restored permissions block this attack, but a software upgrade remains recommended.

The report already contains the student's name and HDU ID. Add the variant number after the instructor assigns it. Submit the English report and ZIP through the course platform with the repository and successful CI links. The report is excluded from the public repository because it contains personal cover-page details.

The Chinese submission ZIP from the earlier draft is retained as a backup. Use `Work1_Submission_23320321_EN.zip` for the English submission.
