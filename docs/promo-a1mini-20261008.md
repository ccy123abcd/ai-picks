# A1 Mini 促销标注 — 即插即用片段（2026-10-08 备好）
大促结束时间：今晚 23:59（美西时间，PDT）。过了就别上。

## 背景（用户已纠正，用户说的为准）
- $249 是 **A1 Mini 单色基础版 + LED Kit**（USD，约 CA$344），不是站里列的 A1 Mini Combo 多色版。
- 早先建议的标注位置是错的：不能直接把 $249 标在 A1 Mini Combo 条目上，会误导。
- 用户三选一：①条目加修正注（写清是单色版）②指南顶部加横幅 ③跳过。用户尚未拍板。

## 方案 A：指南顶部横幅（插到 `<p class="meta">…</p>` 之后）
用 matrix 主题配色（黑底+琥珀黄），过期即删。

```html
<div style="background:#141000;border:1px solid #e0a500;border-radius:10px;padding:.9rem 1.1rem;margin:1.25rem 0;color:#e8e2c8">
<strong style="color:#ffd54a">⏳ 限时促销 · 今晚 23:59（美西）结束</strong><br>
Bambu Lab <strong>A1 Mini 单色基础版 + LED Kit 官方直降 $249</strong>（约 CA$344）——新手最低门槛。注意：是单色基础版，不是多色 Combo 版。
</div>
```

## 方案 B：A1 Mini Combo 条目修正注（插到 A1 Mini Combo 卡片的 `Best for:` 段落之后）
文件 `human/best-3d-printer-2026.html` 的 A1 Mini Combo 卡片里，
`<p style="color:#888;font-size:.85rem">Best for: Best for beginners — easiest first printer - $299-$459</p>`
后面加：

```html
<p style="color:#ffd54a;font-size:.85rem;margin-top:.5rem">⏳ 限时：官方 A1 Mini 单色基础版+LED Kit $249（约 CA$344，今晚 23:59 美西结束）——是单色版，不是多色 Combo 版。</p>
```

## 两个版本都要动
- `human/best-3d-printer-2026.html`（人类版）
- `ai/best-3d-printer-2026.html`（AI 版）——先确认同样有 A1 Mini Combo 卡片，片段同样适用

## 上线流程（发布=对外发布，需用户批准）
1. 用户选 A 或 B（或跳过）
2. 编辑 human/ai 两个文件
3. 按 ai-picks 流程部署：生成器输出到 output/ → `cp -r output/* .` 同步到根目录（Pages 从根目录部署）→ git commit + push
   （注意推送用 `~/.ssh/ai_picks_key` + 代理，见 AGENTS.md；直连 ssh.github.com 会被代理 reset）
4. 大促结束后撤下片段（标注有过期时间，过期即撤）

## 校验建议
- 打开 https://aivaultpro.com/human/best-3d-printer-2026.html 确认横幅/注渲染正常
