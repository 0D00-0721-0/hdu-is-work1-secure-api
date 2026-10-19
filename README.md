# Work 1 - Secure REST API + CI security scanning + Vulhub CVE

本项目对应《Labs Full Manual HDU IS》Work 1（第 1-5 页）。实现 Python 3.12 + Flask + SQLite 安全 API，并在本机 Docker 中验证 Apache HTTP Server CVE-2021-41773 的复现和修复。

## 1. 交付与证据

- `app/`、`run.py`：安全 API。
- `requirements.txt`：运行依赖的固定版本及 SHA-256 哈希。
- `requirements-dev.txt`：固定版本的测试与扫描工具及其依赖。
- `.github/workflows/ci.yml`：push、pull_request、手动触发的 CI。
- `tests/test_api.py`：29 项认证、输入处理、SQLi、XSS、权限与回归测试。
- `scripts/curl_tests.sh`：真实 HTTP 的 curl 验证。
- `lab/vulnerable/`：来自 Vulhub 的漏洞 Dockerfile 和上游说明。
- `fixes/`：修复 Dockerfile、Compose、差异补丁与修复说明。
- `evidence/`：本次实际运行的原始日志、HTTP 响应和扫描 JSON。
- `docs/SCREENSHOTS.md`：截图与原始证据对照表。
- 完整实验报告在本地提交包中，包含封面资料；为避免公开学号，不纳入公开仓库。

本地已实际通过的结果见 [验证记录](evidence/VERIFICATION.md)。远程仓库与最后一次成功 CI 链接见 [提交信息](docs/SUBMISSION.md)。扫描结果只表示所列工具在记录时间和扫描范围内未发现问题。

## 2. 安装与运行

要求 Python 3.12、pip、Git。CVE 部分另需 Docker Desktop 与 Docker Compose V2/V5；Apple Silicon 通过 `linux/amd64` 运行上游旧镜像。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-dev.txt
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python -m flask --app app:create_app init-db
python -m flask --app app:create_app create-user --login student
python run.py
```

创建用户时交互输入至少 12 个字符、至多 72 个 UTF-8 字节的密码。不要把真实账号密码用于实验。数据默认存于 `instance/work1.sqlite3`，不会进入 Git。可用 `DATABASE_PATH` 指定其他数据库路径。服务默认监听 `http://127.0.0.1:5001`，使用 Waitress，未开启 Flask debug。

`JWT_SECRET_KEY` 不写入源码，也不提供固定默认值。新终端启动时重新设置会使旧令牌失效；需要跨重启保留会话时应通过本地秘密管理方案保留同一随机密钥。不要提交该密钥。

## 3. API

| 方法 | 路径 | 认证 | 输入与输出 |
| --- | --- | --- | --- |
| POST | `/auth/login` | 不需要 | JSON `login`、`password`；成功返回 JWT、Bearer 类型和 900 秒有效期 |
| GET | `/api/data` | Bearer JWT | 返回当前用户的登录名和本人笔记列表 |
| POST | `/api/notes` | Bearer JWT | JSON `title`、`body`；创建本人笔记，返回 201 |

```bash
# 密码请替换为自己创建的实验密码；不要在共享终端展示真实密码。
curl --noproxy '*' -i http://127.0.0.1:5001/api/data
curl --noproxy '*' -sS http://127.0.0.1:5001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"student","password":"YOUR_LAB_PASSWORD"}'

# 将登录返回的 access_token 放入 TOKEN（不要把令牌提交到仓库）。
read -r -s TOKEN
curl --noproxy '*' -i http://127.0.0.1:5001/api/data \
  -H "Authorization: Bearer $TOKEN"
curl --noproxy '*' -i http://127.0.0.1:5001/api/notes \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Study plan","body":"Review JWT and parameterized SQL."}'
unset TOKEN
```

完整 curl 脚本不会打印密码或有效 JWT。在另一个已启用虚拟环境的终端运行：

```bash
bash scripts/curl_tests.sh
# 非默认用户名：LAB_LOGIN=alice bash scripts/curl_tests.sh
```

未提供令牌、伪造令牌、签名错误、过期或尚未生效、issuer/audience 不匹配、缺少必要声明和不存在的用户均拒绝访问。错误密码和不存在的账号使用同一 401 提示。格式错误 JSON 返回 400，非 JSON 返回 415，超出请求上限返回 413。

## 4. 安全措施

### SQL 注入防护

所有带用户输入或身份标识的查询均通过 SQLite `?` 占位符绑定，例如：

```python
db.execute("SELECT id, password_hash FROM users WHERE login = ?", (name,))
db.execute("SELECT id, title, body FROM notes WHERE user_id = ? ORDER BY id", (g.user["id"],))
```

查询结构与数据分开处理。`' OR 1=1 --` 被当作登录名，无法绕过认证；笔记里的 SQL 字符串作为普通文本保存，不执行。`executescript` 仅用于源码中的固定建表语句。

### XSS 防护

原始文本保存在数据库，所有返回给客户端的用户字符串在响应边界通过标准库 `html.escape(..., quote=True)` 转义，包括笔记标题、正文和登录名。例如 `<script>` 返回为 `&lt;script&gt;`。POST 创建和 GET 再读取采用同一规则，避免重复存储转义。

接口返回 `application/json`，设置 `X-Content-Type-Options: nosniff`、`Cache-Control: no-store` 和限制性 CSP。将来添加前端时，应使用 `textContent` 和对应上下文的输出编码；HTML 文本转义不等于 JavaScript、URL 或 CSS 上下文的通用净化。

### 密码与 JWT

- bcrypt 随机盐，cost=12，仅存哈希；限制 72 字节以避免 bcrypt 输入截断问题。
- 不存在的账号也执行一次相同成本的 bcrypt 校验，减少直接的账号枚举时序差异。
- JWT 固定 `HS256` 算法，校验签名和 `exp`、`iat`、`nbf`、`sub`、`iss`、`aud`、`jti`；有效期 15 分钟。
- 两个业务接口共用认证装饰器，并确认用户仍存在；按 JWT 对应的用户 ID 查询/写入，不接受客户端指定所有者。
- 启动时拒绝缺少或短于 32 字节的签名密钥；令牌中不含密码和哈希。JWT 负载可解码，不能当作加密存储。

### 输入约束与范围

请求体上限 16 KiB；标题 1-100 字符且非全空白，正文至多 2000 字符；严格校验 JSON 对象、字段与类型。课程范围以外尚需生产级 TLS、登录速率限制、密钥轮换、注销/撤销策略、结构化审计和备份。`jti` 已签发但未实现撤销列表。

## 5. CI：SAST + SCA + tests

```bash
mkdir -p reports
python -m pytest -q --junitxml=reports/pytest.xml
bandit -r app run.py -f json -o reports/bandit.json
pip-audit -r requirements.txt --require-hashes -f json -o reports/pip-audit.json
```

CI 使用独立的 tests、sast、sca 矩阵任务；任何一个失败都会使对应检查失败，其他检查仍运行。无 `continue-on-error`。报告通过 `always()` 上传，保留 30 天。GitHub Actions 权限仅 `contents: read`，第三方 Action 固定到经核验的提交 SHA，依赖安装使用固定版本和哈希。

Bandit 的范围为安全 API（`app/` 和 `run.py`）。故意脆弱的 Vulhub 环境单独放在 `lab/`，不会混入 API 扫描。Bandit 将标准字符串 `token_type: Bearer` 误报为固定密码；只在该行使用带注释的 `# nosec B105`，其他检查保留。SCA 审计 `requirements.txt` 的全部 10 个运行依赖；不把工具依赖的扫描结果混称为运行依赖结果。

按本次任务要求使用 Bandit + pip-audit；手册 SCA 举例为 OWASP Dependency-Check/Snyk，pip-audit 是本项目选择的 Python 专用替代工具。如教师限定工具名称，需另补对应扫描。

## 6. Vulhub CVE 的选择与实际复现

手册提到的 `vulhub/flask/CVE-2018-1000656` 在本次检查的 Vulhub 提交中不存在，Flask 目录只有 `ssti`；后者没有对应的该 CVE，不能冒充它。CVE-2018-1000656 实际是旧 Flask 的 JSON 编码处理导致内存消耗/DoS。手册允许选择其他常见服务，因此选择现存的 `httpd/CVE-2021-41773`。

上游仓库：<https://github.com/vulhub/vulhub>，检查的提交 `9b90d4276f84feed6333286afeb7e1250379a1da`。本地保留上游 Dockerfile、README 和 MIT 许可证；本项目 Compose 将端口从全接口 8080 改为仅回环 `127.0.0.1:18080`，并加上资源限制、`no-new-privileges`，没有挂载主机敏感目录。

```bash
git clone --depth 1 https://github.com/vulhub/vulhub.git third_party/vulhub
# 对照上游 third_party/vulhub/httpd/CVE-2021-41773/README.md 和 Dockerfile。
docker compose -p work1-cve -f lab/vulnerable/compose.yml up --build -d
docker compose -p work1-cve -f lab/vulnerable/compose.yml ps
docker compose -p work1-cve -f lab/vulnerable/compose.yml exec -T apache httpd -v
bash scripts/verify_cve.sh vulnerable
```

核心只读复现请求（目标只允许是本地实验容器）：

```bash
curl --noproxy '*' --path-as-is -i \
  'http://127.0.0.1:18080/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd'
```

`--path-as-is` 防止 curl 在发送前规范化路径。本次读取的是容器的 `/etc/passwd`，不涉及主机文件。实验验证文件泄露，不执行 RCE。具体状态码和响应保存在 `evidence/cve-vulnerable/`。

## 7. 根因、修复与回归

Apache 2.4.49 的路径规范化对编码后的 `..` 处理不完整。请求经 `/icons/` 的 Alias 映射后能够越出预期目录；Vulhub 又把根目录的 `Require all denied` 改成 `Require all granted`，使越界文件可以被访问。上游还启用 CGI，满足其他条件时可能扩大为命令执行，本次不验证该分支。

Apache 2.4.50 对 CVE-2021-41773 的初次修复仍不完整，产生相关 CVE-2021-42013；2.4.51 才修复后者。本项目不把 2.4.50 当作完整的最终修复，采用本次核查的 Apache 2.4.69 官方镜像，同时恢复默认根目录拒绝、未启用 CGI 和未额外开放 Alias 的配置。

```bash
docker compose -p work1-cve -f lab/vulnerable/compose.yml down
docker compose -p work1-fixed -f fixes/compose.yml up --build -d
docker compose -p work1-fixed -f fixes/compose.yml exec -T apache httpd -v
bash scripts/verify_cve.sh fixed
docker compose -p work1-fixed -f fixes/compose.yml down
```

修复后的验证脚本重发完全相同的原始攻击 URL，要求返回 400/403/404 且正文不含容器账户文件内容；同时首页必须返回 200 和 `It works!`。这是综合版本与配置修复的验证，不把结果单独归因于其中一个改动。修复细节和 diff 见 `fixes/README.md`、`fixes/httpd.patch`。

另外完成了独立的配置缓解对照：`fixes/compose.mitigation.yml` 使用同一 2.4.49 基础镜像、保留 autoindex Alias，但保持文件系统根目录默认拒绝且不开 CGI。它在 18081 端口实际把相同攻击从 200 阻断为 403，同时首页仍为 200；这不代表旧版二进制缺陷已被移除。运行方法为 `BASE_URL=http://127.0.0.1:18081 bash scripts/verify_cve.sh fixed evidence/cve-mitigation`。最终升级验证状态见验证记录。

首次镜像下载因当前网络 DNS/IPv6 不通失败，后续网络恢复后成功。临时 Wi-Fi DNS 已恢复自动获取，Docker 代理设置未改动。没有使用上游示例图片替代本机证据；日志页面截图明确标注其来源。

## 8. Git 初始化与提交

项目目录已初始化本地 Git，并有提交记录。压缩包不包含 `.git`、本地数据库、密码和 JWT 密钥。解压后可重建仓库：

```bash
git init -b main
git add .
git commit -m "Complete Work 1 secure API and CVE verification"
gh auth status
# 需要另建仓库时，先登录自己的 GitHub，再执行：
gh repo create work1-secure-api --public --source=. --remote=origin --push
gh run list --workflow ci.yml
```

公开仓库中仅放可公开的代码、实验日志和技术文档；包含姓名、学号的封面报告保留在本地提交包。若要交到教学平台，提交压缩包与报告，并填入 `docs/SUBMISSION.md` 中的仓库/成功流水线链接。

## 9. 参考资料

1. 课程手册：《Labs Full Manual HDU IS》，Work 1，第 1-5 页。
2. [Vulhub CVE-2021-41773](https://github.com/vulhub/vulhub/tree/9b90d4276f84feed6333286afeb7e1250379a1da/httpd/CVE-2021-41773)。
3. [Apache 官方漏洞公告](https://httpd.apache.org/security/vulnerabilities_24.html)：CVE-2021-41773、CVE-2021-42013。
4. [NVD CVE-2021-41773](https://nvd.nist.gov/vuln/detail/CVE-2021-41773)。
5. [Flask CVE-2018-1000656 advisory](https://github.com/advisories/GHSA-562c-5r94-xh97)。
6. [Bandit 文档](https://bandit.readthedocs.io/en/latest/)、[pip-audit](https://github.com/pypa/pip-audit)。
7. [PyJWT usage](https://pyjwt.readthedocs.io/en/stable/usage.html)、[Python SQLite 参数绑定](https://docs.python.org/3/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries)。
