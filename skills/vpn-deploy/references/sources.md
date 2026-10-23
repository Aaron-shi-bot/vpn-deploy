# 来源与修正

部署流程整理/核验日期：2026-10-13；公开版整理及应用边界补充：2026-10-23。此日期不保证后续 UI、字段、软件包、价格或安装器不变，执行前核对实际版本。

## 原流程

本技能来自使用者提供的一次私人搭建记录，流程由 VPS 选购延伸到 3x-ui、REALITY、Windows v2rayN 和多设备分发，其中使用者反馈搭建成功。公开版提炼通用步骤，原始分享入口和聊天内容不随仓库分发。

本技能保留操作主线和 UI 障碍，参数化具体机器信息。未保存原聊天全文、真实 VPS 地址、面板路径、账号、密码、UUID、Token，也未登录或测试记录中的服务器。文档采用自主整理的说明，不打包上游程序；上游项目许可由各自仓库提供。

## 官方核对入口

- [3x-ui 仓库](https://github.com/MHSanaei/3x-ui)、[文档](https://docs.sanaei.dev/)：安装、版本、管理及数据库。项目定位以官方说明为准，不承诺企业生产适用性。
- [订阅 API](https://github.com/MHSanaei/3x-ui/blob/main/docs/content/docs/en/reference/api/subscription-server.mdx)、[控制器](https://github.com/MHSanaei/3x-ui/blob/main/internal/sub/controller.go)、[订阅服务](https://github.com/MHSanaei/3x-ui/blob/main/internal/sub/service.go)：按 subId 取配置，不使用 email 查询过滤。
- [REALITY 官方示例](https://github.com/XTLS/REALITY/blob/main/README.en.md)：目标要求、密钥、Short ID 及可选 Vision；本技能选择 Vision 组合。
- [Xray 安全字段](https://github.com/XTLS/Xray-core/blob/main/infra/conf/transport_security.go)、[传输别名](https://github.com/XTLS/Xray-core/blob/main/infra/conf/transport_internet.go)：target/dest、password/publicKey、raw/tcp 的版本与兼容核对，以及目标站告警。
- [v2rayN 发布文件说明](https://github.com/2dust/v2rayN/wiki/Release-files-introduction)、[UI 说明](https://github.com/2dust/v2rayN/wiki/Description-of-some-ui)、[系统代理和路由](https://github.com/2dust/v2rayN/wiki/Description-of-system-proxy-routing)：选包、导入、代理覆盖范围。
- [Let's Encrypt IP 与短期证书](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability)：受信任的 IP 证书可用，不等同自签证书。
- [Claude Code 网络配置](https://code.claude.com/docs/en/network-config)：HTTP/HTTPS 代理与进程配置范围。
- [Anthropic 隐私政策](https://www.anthropic.com/legal/privacy)、[账号警告与申诉](https://support.claude.com/en/articles/8241253-safeguards-warnings-and-appeals)：不能把账号风险简化为中转跳数或只看 IP。
- [Codex 技能文档](https://learn.chatgpt.com/docs/build-skills)：技能安装位置、结构与调用方式。

## 不照搬的结论

| 原流程问题 | 本技能处理 |
| --- | --- |
| 扫描 SSH 端口后被用户叫停 | 直接用已知端口，限目标测试 |
| 独立 Xray 和面板重复安装 | 默认一套面板管理内核 |
| 无检查创建 swap、追加 fstab | 检测现状后按需变更 |
| 要求固定时区、推断网站全部地区判断依据 | 保留时区，只说明不改变公网 IP |
| 将 IP 证书一概视为自签并跳过告警 | 验证 SAN/链/时间/续期或用管理隧道 |
| 永久固定第三方 REALITY 目标 | 实测并检查当前内核告警 |
| RAW 被解释成裸以太网帧 | 此处是 TCP 传输命名 |
| REALITY 与 Vision 被说成必然绑定 | 本路线两端匹配，但其他有效组合不否定 |
| 反复猜客户端区域在页面下方 | 读实际 UI，支持独立客户端管理 |
| 关联入站全选 | 只选当前授权入站 |
| 五设备必须五 UUID | 按独立统计/撤销需要选择 |
| 默认订阅全部客户端，靠 email 参数过滤 | 专属 Sub ID，检查实际返回内容 |
| 非活动节点绝无流量 | 区分探测、在线窗口和活动路由 |
| 代理 UUID 与应用账号风控混为一谈 | 区分认证、出口 IP 与应用账号 |
| 固定排名、价格、零风险保证 | 实时核实且不作账号安全保证 |
| 开放端口就宣称完成 | 服务、握手、出口与应用分层验收 |

这次工作创建技能和离线检查器；文档核验与脚本测试不等于真实 VPS 部署验收。
