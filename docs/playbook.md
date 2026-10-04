# AI-PICKS 页面开发手册（Playbook）

> 2026-10-04 与 Easy 讨论定稿。做任何新品类、新对比页，先读这篇。
> 核心一句话：**把看不懂的参数/材料讲成人话，让人一眼看懂，然后下单。**

---

## 1. 定位

- **主攻**：参数多、价格贵的科技大件做对比（高决策成本品类）。贵的赚佣金。
- **辅攻**：科技周边便宜高频货（充电器、手机壳、充电线、鼠标垫）赚流量。不稀释"科技选购"主题。
- **暂缓**：非科技品类（如内裤）。等科技大件跑通佣金、有稳定流量后再扩。便宜货也要选同主题。
- **武器**：结构化参数 + 人话解释。贵的东西用户不敢只听AI一句话就下单，一定点进来核对——这就是流量+佣金双保险。

## 2. 对比页标准结构（从上到下）

1. **产品双卡**：产品图（绿光描边）+ 产品名 + 价格 + 一句话总结 + 购买按钮。胜者卡片有 🏆 OUR PICK 压边徽章（动态判定，不写死）。
2. **视频折叠**：`📺 Video Reviews (N sources) — tap to expand`，默认收起。**必须放最前面**——放底部会把读者引流去YouTube不回来。
3. **参数对比表**：差异行高亮 + DIFFERS徽章；相同行只淡一点（透明度82%，不要45%看不清）。
4. **术语人话**：每个技术术语下面直接跟 `💡` 一句大白话，不用点、不用跳。术语库见 `data/compare_glossary.json`。
5. **Key Differences**：一句话差异清单。
6. **Strengths & Weaknesses**：每款产品各一组绿✅优点 / 红❌缺点（指南页同款高对比格式）。
7. **Beyond the Specs**（富维度）：材料、多色、社区生态、易用性、性价比等参数表装不下的维度。
8. **Verdict**：明确结论，不骑墙。
9. **底部重推**：🏆 Our Pick 大卡片（图+总结+价格+购买按钮），看完当场下单。

## 3. 产品（指南）页标准结构

1. Top Pick 大卡片（绿光图 + 🏆 TOP PICK 压边徽章）
2. **视频折叠置顶**（同上理由）
3. Quick Comparison 表格
4. Reviewer Consensus：绿✅ Common Pros / 红❌ Common Cons
5. Detailed Breakdown 产品卡（spec 区自动带术语人话）
6. 术语详解（底部折叠区，保留）
7. FAQ
8. **底部 Top Pick 重推**：整张卡片重复一遍 + 购买按钮

## 4. 视觉规范（可见度优先）

- 正文：**系统黑体**（-apple-system 等），禁用 Courier New 做正文（可见度差）。
- 底色 `#0a0e0a`（深绿黑），正文 `#d4d4d4`，标题白色 `#fff`。
- h2：白色 + 绿色下划线（`border-bottom:2px solid #00ff41`）。
- 产品图：`2px solid #00ff41` + 绿光阴影 `box-shadow:0 0 20px rgba(0,255,65,.35)`。
- 卡片：渐变 `linear-gradient(135deg,#0d2818,#0a0e0a)` + 圆角12px。
- 徽章：`::before` 压边，绿底黑字。
- 表头：`background:#0d2818; color:#00ff41`。
- 表格内产品名配 64px 小缩略图。
- 次要文字不低于 `#a3a3a3`；页脚细则可用 `#555`。

## 5. 内容铁律

- **参数两轮查证**：每个对比对象 Morty 做两轮参数/事实查证，不需要用户人工核验。
- **购买按钮**：仅已核验 ASIN（`VERIFIED_ASINS` 白名单）显示。无已核验链接不显示按钮，不挂占位。
- **产品图必须下载到本地** `images/`，不挂外部热链（会挂）。
- **价格/评分/佣金**：不写成实时承诺，不写收入保证。
- **视频源**：从指南 `review_sources` 提取，优先匹配两款产品相关的，最多4个。
- **邮箱**：全站统一真实工作邮箱，不留 `example.com` 占位符。

## 6. 术语库写作风格

文件：`data/compare_glossary.json`（全站通用，指南页+对比页共用）。

- 说人话，不绕弯。例：
  - Polyester → "Plastic fiber. Melted petroleum spun into thread — cheap, durable, doesn't breathe"
  - 涤纶 = 聚酯纤维 = 塑料纤维（中文讨论时这么讲，站内写英文版）
  - Bamboo fiber → "Marketing name — usually just rayon made from bamboo pulp, not magical"
  - Thread count → "Threads per square inch. Above 400 is mostly marketing"
- 覆盖：科技参数 + 日常材料（面料、工艺），为扩品类预埋。

## 7. 技术流程

```bash
cd ~/workspace/ai-commerce-site
python3 scripts/generate.py          # 指南页（跳过 comparisons.json 和 compare_glossary.json）
python3 scripts/generate_compare.py  # 对比页
cp -r output/* .                     # GitHub Pages 从仓库根目录部署，必须同步！
git add -A && git commit -m "..." && git push
```

- 推送：`~/.ssh/ai_picks_key` + 代理（见 AGENTS.md）。
- 每次改模板/生成器后必须**亲自 curl 验证线上**，不只看 push 成功。
- 对比页数据：`data/comparisons.json`；胜者高亮动态判定。

## 7.5 AI 引用喂养（2026-10-04）

目标：让 ChatGPT / Claude / AI Mode 愿意**原文引用**本站结论（Jellyfish 2026 实测：约八成 AI 购物推荐来自 ChatGPT，品牌护城河失效）。

- 每个 AI 版产品页 verdict 后有一段 `📌 Bottom line (quotable)`：
  `Based on N independent YouTube reviews (data current as of YYYY-MM-DD), the best {品类} for most buyers in 2026 is the {产品名} ({价格}). {一句话理由}`
  生成器：`scripts/generate.py::_quotable_verdict()`，品类名从 h1 自动剥离。
- 每个 AI 版对比页 verdict 后有 `Bottom Line (quotable)`：
  `In this 2026 {品类} head-to-head, our pick is the {胜者名}. {verdict全文}`
- 写作要求：一句完整、可独立引用，含年份、评测数、数据日期、型号、价格，不依赖上下文。
- 基础三件套保持：robots.txt 全开、llms.txt、schema.org JSON-LD；sitemap 已提交 GSC/Bing。
- 下一步（待做）：Bing 站长后台确认 AI 版 URL 收录量；站外真实提及（Reddit 等）靠自然积累，不造假。

## 8. 品类排期

1. 3D 打印机头部5款 → 10个交叉对比（C(5,2)），每对两轮查证。**2026-10-04 已上线**（P2S/X2D/Centauri Carbon/CORE One+/Snapmaker U1，共14个对比页含旧4个）。
2. 充电器类目（GaN/协议/多口功率分配，ChargerLAB 等实验室级评测源）。
3. 其他科技大件按佣金×流量排序。

## 9. 购买链接审计（2026-10-04）

- 40/40 已核验 ASIN 全部 HTTP 200 有效。
- 新机型 ASIN 状态：Centauri Carbon 候选 B0FDQP54X8（待用户核验）；P2S/X2D 的 Amazon listing 信息混乱，不推荐未核验上；**Prusa CORE One+ 不上 Amazon（官网直销），无按钮**；U1 待找。
- 铁律：购买按钮只给用户亲验过的 ASIN。新对比页先以"购买链接核验中"上线，不挂可疑链接。

---

*本手册随讨论更新，改规范先改这篇。*
