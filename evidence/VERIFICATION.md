# 实际验证记录

日期：2026-10-19（Asia/Shanghai）。

| 项目 | 本次实际结果 | 原始证据 |
| --- | --- | --- |
| API 测试 | 29 passed | `pytest.txt`、`pytest.xml` |
| 真实 HTTP curl 检查 | 全部通过 | `curl-tests.txt` |
| SAST | Bandit 无未处理告警；一处 Bearer 常量误报采用行级 B105 注释 | `bandit.json`、`bandit-console.txt` |
| SCA | 10 个运行依赖，无已知漏洞 | `pip-audit.json`、`pip-audit-console.txt` |
| Docker | 引擎 29.8.2，Docker Desktop 4.95.0，Compose 5.6.0 | 构建与容器日志 |
| 脆弱环境 | Apache 2.4.49，首页 200，目录穿越 200，读取容器 `/etc/passwd` | `cve-vulnerable-*`、`cve-vulnerable/` |
| 配置缓解 | Apache 仍为 2.4.49；相同路径 403，正常首页 200 | `cve-mitigation-*`、`cve-mitigation/` |
| 升级环境 | 2.4.69 及 Alpine 变体元数据可访问，部分镜像层下载停滞；未完成动态验证 | `docker-fixed-build.txt`、`docker-upgrade-download.txt` |
| GitHub Actions | tests、sast、sca 全部成功，运行 39196313211 | `ci-current/`、`docs/SUBMISSION.md` |

首次网络失败说明：Docker 镜像层下载域名返回了不可达的 IPv6，出现 `no route to host`。临时使用 IPv4 可解析 DNS 后镜像下载成功；随后 Wi-Fi DNS 已恢复原来的自动获取。用户同时切换了网络，不能据此断言成功完全由单一网络改动造成。没有修改 Docker 代理，也没有把失败声称为成功复现。

上述 Bandit 和 SCA 的“无问题”限定于所述扫描范围、规则/漏洞库及记录时间，不代表不存在所有安全风险。
