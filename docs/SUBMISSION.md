# Repository and CI Links

Public repository: [hdu-is-work1-secure-api](https://github.com/0D00-0721-0/hdu-is-work1-secure-api).

Latest successful implementation/submission run: [tests, SAST, and SCA](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39366086767), for commit `c3553cb7106772ef0a1c0c7130f39f936b1476a2`.

The earlier successful [run 39196313211](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39196313211) corresponds to commit `d2cf03c750b7b2d540ee3ea5dfe2b758fdcd272f`. Its downloaded reports and log are in `evidence/ci-current/`. Reports from the first successful run are retained in `evidence/ci/`.

Each subsequent push or pull request triggers the same checks. View the [Actions page](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions) for the latest run. The links above refer to verified successful historical runs, not an assumed result for an unfinished run.

Local results: 29 automated tests passed and all live curl checks passed. The vulnerable AJP request returned 200 and disclosed `/WEB-INF/web.xml`; the mitigation and the Tomcat 9.0.31 upgrade both refused the AJP request, with the homepage returning 200 in all cases. Original evidence is in `evidence/`.

The local report includes personal cover-page details and is therefore not committed to the public repository.
