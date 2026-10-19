# 提交入口

公开仓库：https://github.com/0D00-0721-0/hdu-is-work1-secure-api

已验证成功 CI：https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39196313211

| 提交项 | 文件/位置 |
| --- | --- |
| 项目、运行说明、安全措施与复现步骤 | `README.md` |
| 实验报告草稿 | 本地提交包 `docs/Work1_Report.pdf`，可编辑文本 `docs/Work1_Report.md` |
| 三接口、安全代码、固定依赖 | `app/`、`run.py`、`requirements*.txt` |
| push/PR 安全 CI | `.github/workflows/ci.yml` |
| curl 与自动测试 | `scripts/curl_tests.sh`、`tests/test_api.py` |
| Vulhub 漏洞环境与来源 | `lab/` |
| 已验证配置缓解与升级方案 | `fixes/` |
| 原始运行证据、CI 报告 | `evidence/` |
| 截图与对应清单 | `screenshots/`、`docs/SCREENSHOTS.md` |

本次实际完成：29 项自动测试、真实 HTTP 检查、Bandit SAST、pip-audit SCA、真实 GitHub Actions、Docker/Vulhub 文件泄露复现、配置缓解后 403 和正常首页回归。

范围说明：新版 Apache 镜像的部分层下载停滞，升级方案尚未完成动态验证；已验证的保护措施是 `Dockerfile.mitigation` 和 `compose.mitigation.yml`。这仍使用 2.4.49 二进制，恢复权限可阻断本次攻击，但应继续升级。报告分别记录了这些结论。

待教师通知后，只需补封面的变体编号；姓名与 HDU 学号已填入本地报告。项目和成功 CI 已建好，无需再登录 GitHub 才能查看公开结果。按教学平台要求上传本地报告与 ZIP；报告含学号，不放进公开仓库。
