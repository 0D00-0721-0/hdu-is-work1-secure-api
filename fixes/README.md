# CVE-2021-41773 Protection Measures

The upstream vulnerable settings are retained in `lab/vulnerable/Dockerfile`. This directory contains a **verified configuration mitigation** and a separate **upgrade proposal that has not been dynamically verified**.

| File | Purpose |
| --- | --- |
| `Dockerfile.mitigation` | Uses the cached 2.4.49 base; keeps the autoindex Alias, retains default root-directory denial, and does not enable CGI |
| `compose.mitigation.yml` | Independent mitigation environment on loopback port 18081 |
| `Dockerfile` | Proposed upgrade to official Apache 2.4.69 with its default access/module settings |
| `compose.yml` | Upgrade environment on loopback port 18080, with amd64 compatibility and resource restrictions |
| `httpd.patch` | Unified diff from the vulnerable Dockerfile to the upgrade proposal |
| `../scripts/verify_cve.sh` | Replays the same attack path and checks normal homepage functionality |

## Verified configuration mitigation

Vulhub enables CGI and an autoindex Alias and changes `<Directory />` to `Require all granted`. The mitigation keeps the Alias for comparison, but leaves the default `Require all denied` policy for the filesystem root and does not enable CGI.

```bash
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml up --build -d
BASE_URL=http://127.0.0.1:18081 \
  bash scripts/verify_cve.sh fixed evidence/cve-mitigation
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml down
```

Observed result: the same attack path changed from HTTP 200 to HTTP 403, while the homepage still returned HTTP 200. The old 2.4.49 parser defect remains in the binary. Access restrictions block the demonstrated attack, but a later configuration change could re-expose it; upgrading is still recommended.

## Upgrade proposal and verification limit

Apache 2.4.50 is not the final upgrade target because its fix for CVE-2021-41773 was incomplete; the related bypass is CVE-2021-42013, fixed in 2.4.51. This proposal selects the inspected official 2.4.69 image. It also removes the deliberately weakened Vulhub settings and retains the official defaults for root-directory denial, CGI, and Alias exposure.

```bash
docker compose -p work1-fixed -f fixes/compose.yml up --build -d
bash scripts/verify_cve.sh fixed
docker compose -p work1-fixed -f fixes/compose.yml down
```

Some image layers failed to finish downloading, including attempts with an Alpine variant. The commands above are a future verification procedure, not evidence that an upgraded container was successfully run.

Evidence for the completed mitigation includes build logs, `httpd -v`, raw attack headers/body/status, and the normal homepage response. See `evidence/VERIFICATION.md`. The results establish that the recorded attack is blocked by the tested configuration, not that the software is free of all vulnerabilities.
