# 仓库协作约定

- 默认直接在 `main` 修改、提交并推送；只有用户明确要求时才使用其他分支或 Pull Request。
- `adblock.srs` 和 `upstream-revision.txt` 是生成文件，不手动编辑。
- AdGuard DNS Filter 是唯一上游；`allowlist.txt` 只维护必要的个人放行项。
- sing-box 版本默认保持固定，只有明确升级时才调整，并同步验证转换结果。
- 不加入节点、订阅、凭据或完整 sing-box 配置。
