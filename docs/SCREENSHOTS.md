# 截图清单与证据位置

所有截图均应对应本项目的实际运行。原始日志是主证据，不使用上游 README 中的示例截图冒充本次操作。

| 编号 | 应显示的内容 | 对应原始证据 | 状态 |
| --- | --- | --- | --- |
| S01 | curl 真实 API 检查：未登录 401，登录 200，写入 201，SQLi/JWT 拒绝 | `evidence/curl-tests.txt` | 已运行，待截图汇总 |
| S02 | pytest 29 passed | `evidence/pytest.txt`、`pytest.xml` | 已运行，待截图汇总 |
| S03 | Bandit 无未处理告警，包含扫描范围 | `evidence/bandit.json` | 已运行，待截图汇总 |
| S04 | pip-audit 无已知漏洞，10 个运行依赖 | `evidence/pip-audit.json`、`pip-audit-console.txt` | 已运行，待截图汇总 |
| S05 | GitHub Actions tests/sast/sca 三项成功及 run URL | `docs/SUBMISSION.md`、`evidence/ci/` | 待远程 CI |
| S06 | 漏洞版本 2.4.49、容器回环端口、同一请求读取容器账户文件 | `evidence/cve-vulnerable-version.txt`、`cve-vulnerable/` | 已运行，待截图汇总 |
| S07 | 修复版本、原攻击请求被拒绝且首页仍正常 | `evidence/cve-fixed-version.txt`、`cve-fixed/` | 等待修复镜像 |
| S08 | 修复差异、恢复默认权限、不启用 CGI | `fixes/httpd.patch`、`fixes/README.md` | 已提供 |

截图时请隐藏密码、有效 JWT、任何密钥；保留命令、状态码、版本、运行链接和时间。若通过本地证据页面截图，应标注“原始日志的浏览器呈现”，不要标作终端截图或 Actions 页面截图。
