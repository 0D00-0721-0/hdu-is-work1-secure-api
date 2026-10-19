# CVE-2021-41773 修复附件

`lab/vulnerable/Dockerfile` 保留 Vulhub 的上游脆弱设置；本目录是修复后的实际构建文件。

| 文件 | 作用 |
| --- | --- |
| `Dockerfile` | 将 Apache 2.4.49 升级到 2.4.69，并保留官方默认权限和模块配置 |
| `compose.yml` | 本地回环端口 18080、amd64 兼容、资源限制和 no-new-privileges |
| `httpd.patch` | 脆弱 Dockerfile 到修复 Dockerfile 的统一差异 |
| `../scripts/verify_cve.sh` | 修复前后使用相同请求进行自动验证 |

Vulhub 为方便演示启用 CGI、自动索引 Alias，并把 `<Directory />` 设为 `Require all granted`。修复删除这些有意放宽的设置，恢复官方镜像对文件系统根目录默认拒绝，仅开放正常网页目录。升级补上路径规范化缺陷；权限最小化进一步限制意外的目录映射。

不采用 2.4.50 作为最终修复，因为该版本对 CVE-2021-41773 的修复不完整，相关绕过另编号为 CVE-2021-42013。2.4.51 是后者的历史修复版本；本项目实际选用 2.4.69。该验证仅证明记录的攻击请求被本配置阻断，不等同于整个软件不存在其他漏洞。

运行与关闭：

```bash
docker compose -p work1-fixed -f fixes/compose.yml up --build -d
bash scripts/verify_cve.sh fixed
docker compose -p work1-fixed -f fixes/compose.yml down
```

保留的证据包括构建日志、`httpd -v` 输出、同一攻击的原始响应头/正文/状态码、正常首页响应。见 `evidence/VERIFICATION.md`。
