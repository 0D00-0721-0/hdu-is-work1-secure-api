# CVE-2020-1938 (Ghostcat) Protection Measures

The upstream vulnerable environment is retained in `lab/vulnerable/compose.yml` (Vulhub `vulhub/tomcat:9.0.30`). This directory contains a **verified configuration mitigation** and a **verified version upgrade**.

| File | Purpose |
| --- | --- |
| `Dockerfile.mitigation` | Keeps 9.0.30 but removes the AJP connector from `conf/server.xml` |
| `compose.mitigation.yml` | Independent mitigation environment on loopback HTTP port 18081; AJP is not published |
| `Dockerfile` | Verified upgrade to official Tomcat 9.0.31; restores the default web applications for the homepage check |
| `compose.yml` | Upgrade environment on loopback HTTP port 18082; AJP is not published |
| `../scripts/ghostcat_read.py` | Minimal AJP13 client that requests `/WEB-INF/web.xml` |
| `../scripts/verify_cve.sh` | Replays the AJP read and checks the homepage |

## Verified configuration mitigation

Tomcat 9.0.30 still enables the AJP connector on port 8009. The application only needs HTTP, so the mitigation removes the connector:

```bash
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml up --build -d
BASE_URL=http://127.0.0.1:18081 AJP_PORT=18019 \
  bash scripts/verify_cve.sh fixed evidence/cve-mitigation
docker compose -p work1-mitigation -f fixes/compose.mitigation.yml down
```

Observed result: the AJP request is refused, no file content is returned, and the HTTP homepage returns 200. The 9.0.30 binary remains, but the AJP attack surface is removed.

## Verified version upgrade

Tomcat 9.0.31 is the first 9.0.x release with the CVE-2020-1938 fix. The official image does not enable AJP by default; the Dockerfile restores the default web applications so the homepage can be checked.

```bash
docker compose -p work1-fixed -f fixes/compose.yml up --build -d
docker compose -p work1-fixed -f fixes/compose.yml exec -T tomcat \
  sh -c 'java -cp $CATALINA_HOME/lib/catalina.jar org.apache.catalina.util.ServerInfo | head -1'
BASE_URL=http://127.0.0.1:18082 AJP_PORT=18029 \
  bash scripts/verify_cve.sh fixed evidence/cve-fixed
docker compose -p work1-fixed -f fixes/compose.yml down
```

Observed result: the container reports Apache Tomcat/9.0.31; the AJP request is refused, no file content is returned, and the HTTP homepage returns 200. Evidence is in `evidence/cve-fixed/`.

A deployment that needs AJP should bind it to a trusted interface, set `secretRequired="true"` with a strong secret, and firewall port 8009. This lab leaves AJP disabled because the application does not use it.
