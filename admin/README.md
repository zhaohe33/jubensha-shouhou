# Cloudflare Pages 后台管理

后台地址：`https://jubensha-shouhou.pages.dev/admin/`

## 设置管理令牌

在终端执行（将 `你的强密码` 换成自己的令牌）：

```bash
wrangler pages secret put ADMIN_TOKEN --project-name=jubensha-shouhou
```

按提示输入令牌。设置后需重新部署一次（push 或 `wrangler pages deploy dist`）才会生效。

## 功能

- 查看所有玩家创作的售后（KV 全量列表）
- 统计：总数 / 公开 / 私密 / 含图 / 剧本数
- 搜索与筛选
- 详情：正文、配图、主题、链接
- 导出 JSON
- 删除单条记录

## 安全说明

- `/admin/` 不在站内导航中露出，仅知道地址和令牌者可访问
- 令牌保存在浏览器 `sessionStorage`，关闭标签页后需重新登录
