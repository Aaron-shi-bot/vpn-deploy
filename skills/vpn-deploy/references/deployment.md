# VPS → 3x-ui → REALITY → v2rayN

命令按标注平台运行。尖括号是待替换参数，不能直接执行。默认适用仍受支持的 Debian/Ubuntu 与 systemd，其他系统按官方文档适配。本文件不是自动执行脚本。

## 1. 参数与恢复入口

| 参数 | 来源与处理 |
| --- | --- |
| VPS 地址、SSH 用户与端口 | 实例面板或已确认配置；随机端口不能按 22 猜 |
| OS、架构、内存、磁盘 | 登录后实读，不用教程固定系统覆盖现有系统 |
| NODE_PORT | 通常可用 TCP 443，先排除网站等占用；否则确定空闲端口 |
| PANEL_PORT、管理路径 | 安装结果/面板设置；与节点端口区分，完整私密路径不进公开报告 |
| 管理方式 | 有效 HTTPS，或 SSH 隧道到仅回环监听的 HTTP 面板 |
| REALITY_TARGET、SNI | 从 VPS 实测满足当前内核要求的目标，不固定第三方网站 |
| 客户端范围 | 几台设备/几个人，是否需独立统计、限额或撤销 |

仅在尚未购买或用户要求比较时选购：看地区、实际往返路线、晚高峰表现、带宽/流量计费、支持系统与条款。原聊天中的商家排名、价格、库存、换 IP 承诺不作当前事实。代理与远程开发构建分别评估资源。

Windows PowerShell 连接，密码由用户在终端输入，优先已有密钥：

```powershell
ssh -p <SSH_PORT> <SSH_USER>@<VPS_HOST>
```

首次连接核对主机指纹；已有指纹改变时确认重装/迁移，不盲删 known_hosts。保持会话和服务商控制台恢复入口。

Linux 只读检查：

```bash
cat /etc/os-release
uname -m
free -h
swapon --show
df -h /
timedatectl status
sudo ss -lntp
systemctl status x-ui --no-pager
systemctl status xray --no-pager
```

未安装的 unit 不存在是预期；出现两个代理服务先辨认谁管理已有节点。

## 2. 更新、swap 与时钟

新机器可更新索引、安装依赖；已有业务先检查影响，不自动全量无人值守升级/重启。

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
```

系统升级时读实际交互提示。SSH、sshd_config.d、cloud.cfg 有定制时，先看差异，保留有效配置再合并所需更新，不一律覆盖，也不将所有提示等同于“回车”。修改 SSH 后先 `sudo sshd -t`，核实有效端口、认证和防火墙，再 reload 对应服务并测试第二个会话。

swap 按内存压力需要设置，不是“1GB 必做 2GB”的协议要求。已有 swap 不重复添加。检查 `swapon --show`、fstab、目标文件存在性和磁盘空间后，才为不存在的新文件生成创建命令；不能对已有 `/swapfile` 运行 `mkswap`。fstab 先备份、避免重复行；启用后验证 `swapon --show`、`free -h`。文件系统不支持所选方式时按 OS 文档处理。

时区仅改变时间显示，不改变公网出口。默认保留；用户要求才改为 Asia/Shanghai 或 America/Los_Angeles，实际偏移随夏令时而变。检查 NTP 与系统时间。BBR 不是握手前提；按性能需要检查可用算法后调整，不强制换内核。

## 3. 3x-ui 与管理入口

已有面板先备份数据库、设置与证书并记录恢复方式，不再安装另一套独立 Xray。SQLite 采用面板导出或数据库一致性备份，不随意复制活动数据库作为可靠备份；备份含秘密，限制访问。

查 [官方仓库](https://github.com/MHSanaei/3x-ui) 与 [发布页](https://github.com/MHSanaei/3x-ui/releases)，选择并记录稳定 tag。先保存安装器，审阅来源与行为，再执行：

```bash
curl --fail --location --proto '=https' --tlsv1.2 \
  https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh \
  -o /tmp/3x-ui-install.sh
less /tmp/3x-ui-install.sh
sudo bash /tmp/3x-ui-install.sh <已核对的稳定tag>
```

下载失败停止，不执行同名旧文件。安装器分支可变；需要重复部署时记录审阅后的哈希，或使用已核对提交的原始文件，同时核对发行资产校验值。不自动选开发版本。

按实际提示选数据库与管理参数。单机少量用户通常 SQLite，已有 PostgreSQL 保留。面板端口避开 SSH、节点及业务占用；随机端口本身不是访问保护。凭据由用户保存在密码管理器。

运行 `x-ui` 查看实际管理菜单，按文字找凭据恢复和证书选项，不写死序号或打印全部 settings 到聊天。忘记密码先检查已保存位置；确需重置再按授权走版本支持的交互入口。

管理入口二选一：

- 有效 HTTPS：域名或当前版本支持的 IP 证书；核对 SAN 覆盖访问地址、信任链、有效期及续期。IP 证书不等于自签，短期证书需确认自动续期有效。
- SSH 隧道：面板 HTTP 仅监听 VPS 回环，不开放公网面板端口。Windows 执行下式，本机访问隧道端口加实际路径：

```powershell
ssh -N -L 127.0.0.1:<LOCAL_PANEL_PORT>:127.0.0.1:<PANEL_PORT> -p <SSH_PORT> <SSH_USER>@<VPS_HOST>
```

这里的 HTTP 只用于 SSH 保护的回环。已有 HTTPS 不随意降级；经隧道使用 HTTPS 仍需证书名称匹配。

防火墙只加必要规则，保留有效 SSH 和现有业务。允许节点 TCP 端口，面板限制管理来源或只走隧道。HTTP-01 需要的 80 端口按签发和续期方案配置，不能签完即关导致续期失败。此路线不因节点用 443 就额外放 UDP 443。

## 4. 创建入站

先读实际 UI；不同版本可能多页签。

| 字段 | 本路线的选择与检查 |
| --- | --- |
| 备注/协议/启用 | 如 personal-node / VLESS / 开启 |
| 监听/端口 | 可达网卡与 NODE_PORT，兼顾 IPv4/IPv6 规则 |
| 传输 | RAW 或旧版 TCP，此处不是裸以太网帧 |
| 安全 | REALITY |
| target / 旧版 dest | 从 VPS 实测的域名与端口 |
| serverNames / SNI | 目标证书覆盖的域名，与客户端匹配 |
| 私钥、公钥 | 新 X25519 密钥对；私钥仅服务端，客户端用相应公钥 |
| shortIds | 非空、偶数长度、最多 16 个十六进制字符，客户端 sid 匹配 |
| Flow | 本路线选 xtls-rprx-vision，在实际客户端/凭据位置配置 |
| VLESS encryption/decryption | 基础路线 none，不把另一类 VLESS 加密按钮当 REALITY 密钥 |
| Fingerprint / uTLS | 客户端支持值，如 chrome，以实际版本为准 |

按 [REALITY 文档](https://github.com/XTLS/REALITY) 验证目标：VPS 可达、TLS 1.3、H2、证书/SNI、重定向行为及当前内核要求，记录时间。原流程的 www.microsoft.com 不能作为永久默认。基础探测：

```bash
openssl s_client -connect <TARGET_HOST>:443 -servername <SNI> \
  -tls1_3 -alpn h2 -verify_hostname <SNI> -verify_return_error </dev/null
```

核对协商协议、ALPN 和验证结果；此探测还不能独自证明目标完全适合，需结合当前文档和内核告警。

原始配置字段随版本变动：旧版 `dest`/`publicKey`/`tcp`，新示例 `target`/客户端 `password`/`raw`。REALITY 的 password 在此指服务端私钥对应的公钥，不是面板密码。分享 URI 仍常用 `pbk`。让面板生成适配其内核的配置，不同时乱填新旧字段。

Vision 是此路线选择，不是所有 REALITY 组合的强制项。已有其他工作方案先判断适配，不强制改造。

## 5. 新建、关联及导出客户端

入站创建后客户端为 0 不算完成：

1. 有独立“客户端管理”页时：生成 UUID、标识与所需 Flow，启用，并只关联本次目标入站，不点“关联全部”。
2. 旧版客户端在入站内部时：根据可见入口展开行或编辑窗口。找不到就读取界面/版本证据，不反复要求滚不存在的区域。
3. 保存后检查启用、关联及计数，核对限额/到期的单位和 0 的含义。
4. 导出该用户的链接/二维码。单入站单凭据通常一条，使用离线检查器做格式检查。

UUID 用于认证、计量与撤销，不产生独立公网 IP。入站的 REALITY 密钥和 Short ID 可共享，不必每加一人就轮换。

## 6. Windows v2rayN

从 [官方发布页](https://github.com/2dust/v2rayN/releases) 按 Windows 架构、内核和运行库需求选稳定包，不固定旧的 With-Core 文件名。按用户已有安装目录约定完整解压到固定可写目录。

只导入本用户配置；本地核对地址、端口、UUID、REALITY、公钥、SNI、sid、Flow。不要把链接上传第三方二维码/解码网站。设为活动节点，执行真连接测试。

读取当前 HTTP、SOCKS 或 mixed 实际监听端口，不能假定 10808/10809 的协议永远不变。先用明确代理做对照测试：

```powershell
curl.exe --proxy "http://127.0.0.1:<HTTP_OR_MIXED_PORT>" --max-time 20 https://api.ipify.org
curl.exe --proxy "socks5h://127.0.0.1:<SOCKS_PORT>" --max-time 20 https://api.ipify.org
```

只执行实际可用的协议分支，并检查 NO_PROXY 未让测试地址绕过代理。`socks5h` 让该请求域名经代理解析；一次查询不是所有应用/IPv6/DNS 流量的证明。

随后开启系统代理验证浏览器；不读系统代理的程序按其当前官方文档配置进程代理，或在需要时启用 TUN 并验证路由/DNS。路由“全局”不等于整机所有应用被接管。

若程序文档支持 HTTP_PROXY/HTTPS_PROXY，先只在当前 PowerShell 会话设置到已验证的 HTTP/mixed 端口，再启动目标程序；记录旧值以便恢复，不直接改系统级变量。不要假定所有 Node/Rust/Python 程序都会自动读取它们。

## 7. 验收与回滚

顺序：内核运行 → 指定端口 → 真连接 → 预期出口 → 目标应用实际请求。VPS 只做代理时，不需在 VPS 安装 Codex。记录结果、时间、模式，不采集账号 Token 或完整请求头。

浏览器通而 CLI 不通时，分别检查进程代理、路由、认证环节。401/403/429 按错误内容及产品官方文档解释，不直接归因为 IP 属性。

验证客户端重新启动后仍可用、退出时系统代理恢复；服务/VPS 重启持久性只在授权范围内测，没测就标记。可建议实际使用时段复测，未被要求不自动创建监控、持续扫描或换 IP。

按本次改动回滚：还原系统代理、进程变量及 TUN；停用本次客户端/入站；恢复配置、数据库和具体防火墙规则。撤销新增 swap 先检查可用内存再 swapoff，只移除本次条目/文件，不把卸载重装当统一回滚。
