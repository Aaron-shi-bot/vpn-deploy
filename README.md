# vpn-deploy · 单台 VPS 直连搭建技能

**把个人代理节点的搭建、排障和多设备管理，整理成能从当前进度继续的操作流程。**

vpn-deploy 是供 AI 助手使用的技能，也可以作为人工操作指南阅读。适合已有或准备使用自有 VPS，希望把客户端连接、出口验证和设备凭据分开管理的人。

默认方案由本机 v2rayN 直连一台 Linux VPS，服务端使用 3x-ui 管理 Xray，协议组合为 VLESS + REALITY + Vision。它是代理节点方案，覆盖哪些应用取决于实际代理模式与路由设置。

## 能帮你做什么

| 场景 | 作用 |
| --- | --- |
| 从已有进度继续 | 检查当前服务和配置，已有可用节点时先排查，避免重复安装 |
| 连接与验收 | 分别确认服务、客户端连接、预期出口和目标应用请求 |
| 常见故障 | 排查“浏览器可用但 CLI 不通”、客户端关联和订阅范围等问题 |
| 多设备管理 | 为设备分配独立凭据，方便单独统计、撤销及处理泄露 |
| 离线检查 | 在本机检查 VLESS 链接结构，不上传或回显链接里的秘密 |

本项目提供技能、文档和检查脚本，没有独立的图形界面。3x-ui 与 v2rayN 是另外获取的上游软件。

## 怎样使用

安装技能后，可向助手发送：

```text
使用 $vpn-deploy，按单台 VPS 直连方案指导搭建。
我已经有 VPS，请先检查已有服务，从当前进度继续。
```

```text
使用 $vpn-deploy，排查 v2rayN 能上网但 Claude Code 无法连接的问题。
先区分本地代理、出口、应用设置与账号错误。
```

```text
使用 $vpn-deploy，为自己的几台设备安排独立凭据，
需要能单独撤销，并确认每份订阅只含授权配置。
```

实际操作前说明服务器、客户端与已有进度；密码、私钥和完整订阅链接使用安全方式提供，不贴到公开 Issue。

## 安装

可在 Codex 中发送：

```text
使用 $skill-installer，从 https://github.com/Aaron-shi-bot/vpn-deploy
安装 skills/vpn-deploy 目录中的技能。
```

也可将整个 `skills/vpn-deploy` 文件夹放入客户端支持的技能目录，保留其中引用的脚本和文档；已有同名技能时先核对差异。

## 文档与脚本

| 入口 | 内容 |
| --- | --- |
| [技能入口](skills/vpn-deploy/SKILL.md) | 适用场景、执行顺序和必要约束 |
| [方案说明](skills/vpn-deploy/references/architecture.md) | 单台直连、中转、应用代理覆盖与使用边界 |
| [搭建流程](skills/vpn-deploy/references/deployment.md) | 按当前环境继续操作的参考 |
| [排障与设备分发](skills/vpn-deploy/references/troubleshooting.md) | 按故障层定位、授权和撤销 |
| [离线检查脚本](skills/vpn-deploy/scripts/check_vless.py) | Python 3.10+，无第三方运行依赖 |
| [回归测试](tests/test_check_vless.py) | 合成数据下的格式及输出检查 |
| [来源与修正](skills/vpn-deploy/references/sources.md) | 上游资料与版本变化 |

## 使用范围

这是按环境推进的操作流程，安装技能本身不会修改网络或连接服务器。离线检查通过只说明格式符合检查规则，真实连接仍需实际验证。

本项目不承诺特定地区、出口 IP 或账号安全结果。仓库只包含通用说明、脚本和合成测试数据；3x-ui、Xray、v2rayN 的获取方式与许可要求以各上游项目为准。
