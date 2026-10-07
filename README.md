# sing-box 广告过滤

面向 sing-box / SMBox 的 DNS 广告过滤规则，由 AdGuard DNS Filter 自动生成 SRS。

[接入说明](#sing-box-使用方式) · [下载 adblock.srs](https://raw.githubusercontent.com/zzpice/sing-box-adblock/main/adblock.srs) · [ZZP · 所有项目](https://zzp.moe/)

[![检查与更新](https://github.com/zzpice/sing-box-adblock/actions/workflows/update.yml/badge.svg)](https://github.com/zzpice/sing-box-adblock/actions/workflows/update.yml)

本仓库以 [AdGuard DNS Filter](https://github.com/AdguardTeam/AdGuardSDNSFilter) 为上游，通过 GitHub Actions 定期转换为 sing-box 二进制规则集 `adblock.srs`。仓库只负责生成规则，不包含节点、订阅或完整 sing-box 配置。

## 文件

- `adblock.srs`：自动生成的 sing-box 二进制规则集。
- `allowlist.txt`：个人白名单，一行一个域名。
- `upstream-revision.txt`：当前构建对应的 AdGuard HostlistsRegistry Git 提交。
- `.github/workflows/update.yml`：自动更新与转换流程。

> `adblock.srs` 和 `upstream-revision.txt` 均为生成文件，不建议手动修改。

## Raw 地址

```text
https://raw.githubusercontent.com/zzpice/sing-box-adblock/main/adblock.srs
```

## 白名单

如果某个域名被误拦截，在 `allowlist.txt` 中加入域名即可：

```text
example.com
```

空行和以 `#` 开头的注释会被忽略。每个条目会转换成 AdGuard DNS Filter 的例外规则，因此同时放行该域名及其子域名。

修改 `allowlist.txt` 并推送到 `main` 后，GitHub Actions 会自动重新生成 `adblock.srs`。

## sing-box 使用方式

将 `adblock.srs` 作为远程二进制 rule-set 引入，并在 DNS 规则中对其执行 `reject`。例如：

```json
{
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "adblock",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/zzpice/sing-box-adblock/main/adblock.srs"
      }
    ]
  },
  "dns": {
    "rules": [
      {
        "rule_set": "adblock",
        "action": "reject",
        "method": "default",
        "no_drop": true
      }
    ]
  }
}
```

具体接入方式应以实际的 sing-box / SMBox 配置结构为准。

## 自动更新

工作流会：

1. 获取 AdGuard HostlistsRegistry `main` 当前提交；
2. 从该固定提交下载 `assets/filter_1.txt`（AdGuard DNS Filter）；
3. 应用 `allowlist.txt`；
4. 使用固定版本的 sing-box 转换为 `adblock.srs`；
5. 仅当生成结果或上游提交发生变化时提交回仓库。

自动任务每周一、周四运行，也支持手动运行；推送到 main 时会重新检查和构建。PR 只运行只读检查。下载转换器后核对 SHA-256；上游为 HTML、类型异常、过大或不足 10,000 条 DNS 规则时停止，不覆盖已有产物。转换成功后分别比较二进制与提交记录，即使二进制相同也更新对应上游提交。

当前转换版本：**sing-box 1.14.2**。

## 本地维护

Python 3.10+、Git 与官方 sing-box 1.14.2，无 Python 第三方依赖：

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build.py --sing-box /path/to/sing-box
```

默认解析上游提交后下载固定版本。复现已有构建时，按 `upstream-revision.txt` 下载对应 `filter_1.txt`，再运行：

```sh
python3 scripts/build.py --sing-box /path/to/sing-box --source filter_1.txt --revision <完整上游提交>
```

`--source` 与 `--revision` 必须一起使用。白名单规范化、源数据检查、临时转换与产物更新都在 `scripts/build.py` 中，CI 不再另维护一份内嵌实现。官方转换器不支持的 AdGuard 规则会报告并略过，结果并不等于完整浏览器广告过滤。

## 上游与许可

广告规则来源于 [AdGuard DNS Filter](https://github.com/AdguardTeam/AdGuardSDNSFilter)，其项目采用 GPL-3.0。当前构建对应的 HostlistsRegistry Git 提交记录在 `upstream-revision.txt`，可据此从 `assets/filter_1.txt` 获取精确的对应源规则。

本仓库采用 [GNU GPL v3](./LICENSE)。

## 项目体系

属于 [ZZP 工具与资源](https://zzp.moe/)。使用、验证与维护方式以本仓库为准。
