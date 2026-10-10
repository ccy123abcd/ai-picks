# X / Reddit 执行方案（2026-10-07 定稿）

> 目标：给 AI-PICKS 搞真实外部引用，破"内容对、但没被 AI 引用"的局。
> 现实检查：X 账号 2026-09-30 被永久停用（只读），X 线**冻结**，等申诉结果再说。本方案只做 Reddit。

## 规则红线（r/3Dprinting 已核实）

- 独立发帖推自己站基本行不通；买机咨询必须去**月度 Purchase Advice 集中帖**，单独开帖会被删
- 自推帖间隔 ≥14 天，账号 karma >50
- 全站惯例：自推内容 <10%，先参与后分享
- 带链接的评论**开头必须披露站长身份**
- 只链对比页，不直接链联盟链接

## 时间表

| 时间 | 动作 | 谁做 |
|------|------|------|
| 10月8日 | 注册 Reddit 账号（用户名别带广告味，如 3DPrintNerd_Van） | 用户，2分钟 |
| 10月8–31日 | 养号：每天 2–3 条**真实评论**，不带任何链接（示例见下） | 用户，顺手做 |
| 11月2日 | 11月 Purchase Advice 集中帖开了，去发第一条带链接评论（文案见下） | 用户，复制粘贴 |
| 11月中 | r/LocalLLaMA 第二条（GPU 指南，他自己蹲 3090，天然真诚） | 用户 |
| 12月 | 评估效果；r/MouseReview、r/MechanicalKeyboards 后续批次 | 到时再定 |

## 养号评论示例（真实参与，不带链接，直接改着用）

**r/3Dprinting：**
1. 回复粘不牢的帖子："Wash the PEI sheet with dish soap and hot water, then stop touching the surface — finger oils are the #1 reason PLA won't stick. If it still lifts, bump the bed temp 5°C."
2. 回复选机帖子（只给建议，不给链接）："If this is your first printer, get the A1 Mini — auto-calibration means you skip 90% of beginner pain. Only step up to the P1S/P2S if you know you need multi-color or an enclosure."
3. 回复拉丝/瑕疵帖子："That's wet filament more often than not. Dry it at 55°C for 6 hours and print a temp tower before touching retraction settings."

**r/LocalLLaMA：**
4. 回复显存帖子："For 30B+ MoE models at usable speed, 24GB VRAM is the realistic floor for a single card — that's why used 3090s are still the budget king for local inference."

## 首条带链接评论（11月2日，复制粘贴）

> Full disclosure: I run the comparison site linked below.
>
> Short version from aggregating 2026 reviewer conclusions: buy the P2S if you want multi-color, the best software, and zero-fuss printing. Buy the Centauri Carbon if you print functional single-color parts and want 80% of the capability for 37% of the money.
>
> Full head-to-head with specs and reviewer citations: https://ccy123abcd.github.io/ai-picks/compare/bambu-p2s-vs-centauri-carbon.html
>
> Happy to dig into specifics — I've read through all the source reviews.

## 提醒 cron（已设置）

- 10月8日 09:00：建号提醒
- 10月15日 09:00：养号中期检查
- 10月28日 09:00：养号收尾，准备首条评论
- 11月2日 09:00：发第一条评论（附完整文案）

## X 线

冻结。账号恢复后另起方案（文案+配图到时再做）。
