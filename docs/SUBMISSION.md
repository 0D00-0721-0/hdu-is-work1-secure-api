# Repository and CI Links

Public repository: [hdu-is-work1-secure-api](https://github.com/0D00-0721-0/hdu-is-work1-secure-api).

Verified successful implementation/submission run: [tests, SAST, and SCA](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39196644394), for commit `885cdb13d27cdff25e4cbf76e0b71df9c9c412da`.

The earlier successful [run 39196313211](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39196313211) corresponds to commit `d2cf03c750b7b2d540ee3ea5dfe2b758fdcd272f`. Its downloaded reports and log are in `evidence/ci-current/`. Reports from the first successful run are retained in `evidence/ci/`.

Each subsequent push or pull request triggers the same checks. View the [Actions page](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions) for the latest run. The links above refer to verified successful historical runs, not an assumed result for an unfinished run.

Local results: 29 automated tests passed and all live curl checks passed. The vulnerable traversal returned 200; configuration mitigation returned 403 for the same path, with the normal homepage returning 200 in both cases. Original evidence is in `evidence/`.

The local report includes personal cover-page details and is therefore not committed to the public repository. Updating the documentation language does not change the original execution timestamps or imply a new CVE experiment.
