# Work 1 提交信息

公开仓库：[hdu-is-work1-secure-api](https://github.com/0D00-0721-0/hdu-is-work1-secure-api)。

已成功的 CI 运行：[tests + sast + sca](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions/runs/39196313211)，对应提交 `d2cf03c750b7b2d540ee3ea5dfe2b758fdcd272f`。运行事件为 push，三项全部成功，报告已保存于 `evidence/ci-current/`。历史首个成功运行保留在 `evidence/ci/`。

之后每次 push/PR 仍会触发同样检查；最新状态可在 [Actions](https://github.com/0D00-0721-0/hdu-is-work1-secure-api/actions) 查看。本页引用的是已验证的成功运行，不使用尚未完成的链接冒充成功。

本地测试：29 项通过；真实 curl 检查全部通过。脆弱环境的目录穿越为 200，配置缓解后为 403，正常首页均为 200。原始证据见 `evidence/`。

提交到教学平台的报告含个人封面资料，因此保留在本地压缩包，不公开提交到 Git。
