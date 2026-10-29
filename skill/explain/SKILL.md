---
name: explain
description: 以流程（Code Atlas tour）为单位把代码讲清楚：主代理只回答、推荐路线、建流程、派活、验收；每一步的动画卡交给全新上下文的子代理做，再交给“新人”子代理审查到看懂。Use when the user asks how something works, says a step is unclear (“这一步没懂”, “流程”, “tour”), wants an explanation saved (“沉淀”, “做成讲解卡”), or asks to explain one function/module in context.
---

# explain：主代理编排，子代理做卡

## 分工（硬规则）

- **主代理（你）**：回答用户、推荐路线、建/改流程、派活、验收、集成。
  **不写卡、不画 SVG、不生成动画、不套模板。**
- **制卡子代理**：一步一张卡。全新上下文，只拿 brief + 这一步的信息。
- **审查子代理**：全新上下文，只当“新人”读卡。

主代理碰卡片只有两件事：验收、把审查意见退回给原 builder。

**预算无上限。** 不要为了省帧、省 token 让 builder 合帧或压缩讲解；只按卡片质量验收。builder 卡住就换一个/补上下文，主代理不自己上手画。

## 唯一入口

1. 先回答用户的问题。
2. 根据问题推荐 **3–5 条粗路线**：名字 / 从哪进 / 到哪产生效果 / 2–4 个关键步。问：“哪条要建？”
3. **用户点了才建**；没点不建流程、不做卡、不挂卡。用户明确说“把 X 做成讲解”也算点了，但仍先确认范围。
4. 建流程：一步一个函数，validate 连通 + 粒度（[references/routes.md](references/routes.md)）。
5. **给流程的每一步各派一个 builder**（一步一个，全部一起派），prompt 用 [references/builder.md](references/builder.md) 填空。builder 做完会自己开 reviewer 审。
6. **派完本轮就结束。** 所有 builder 都回来（或报错）之后，再统一验收：qa → 反模板 → reviewer 结论。
7. 审查：**由每个 builder 自己再开 reviewer 子代理**审卡（[references/reviewer.md](references/reviewer.md)），**最多 2 轮**；只修阻塞问题，2 轮后停。**主代理不派 reviewer，只看结论；发现第 3 轮还在改就叫停。**
8. apply / build / 汇报。

## 不要催子代理

- **不要发消息催进度、不要中途打断、不要因为一时没输出就重启。**
- 只有它**报错**或**明确说卡住**时才处理；否则等它自己回来。
- 等待期间主代理可以整理流程、验收清单、下一张卡的占位，但不要重复派同一个 builder。
- 一次只开一个 builder 做同一步；两个 builder 写同一张卡只会互相覆盖。

## 派 builder 的硬规则

- 必须用 **subagent（全新上下文）**，**绝不用 subagent_fork**，绝不把对话、我的分析、别的卡的实现塞给它。
- **一条流程的每一步各派一个 builder，全部一起派**；不要一个 builder 做多步，也不要一次只派一步慢慢等（单步试点除外）。
- prompt = [references/builder.md](references/builder.md) 填空，只给：repo、step 的 at/text、前后各一步的 text、card id、输出目录、anchors。
- 明确要求 **PTC 模式**：用 run_code 写程序批量读代码、生成、跑 QA，不要一条条手点。
- builder 自己读代码、自己决定图形和帧数；不接受“按我的模板填字”。
- builder 做完后，**必须自己再开一个 reviewer 子代理**（全新上下文、subagent 而非 fork）审这张卡，
  按意见修完再换一个新 reviewer 复读；主代理不参与审查派发。

## 派完就结束

一条流程的 builder 全部派出后，主代理本轮就可以结束，不要守着、不要催。
等所有 builder 都回来（或报错）再开始验收：qa → 反模板 → reviewer 结论 → apply。

## 审查收敛（防跑飞）

reviewer 很容易越提越多，builder 会一直改。必须设停：

- reviewer **只报“阻塞”**：它按帧复述时卡住的地方。排版、措辞、“可以更好”一律标非阻塞，不要求改。
- 每张卡 **最多 2 轮 reviewer**（最多 2 个 reviewer 会话）；不要每轮新开一串。
- builder 只修阻塞条目；非阻塞记下来，不改。
- 2 轮后 reviewer 还说“还有 N 处”，但复述已经通、剩下都是非阻塞 → **停，按通过**。
- reviewer 的要求超出这一步范围、或与代码不符 → builder 拒绝，写进汇报。
- 主代理发现第 3 轮还在改，直接叫停，按当前版本验收。

## 脚本查什么，不查什么

- **qa.mjs**：机械检查——每帧只有一个图层/caption/nav、无文字互叠、光圈不切字、不压框、不出画、
  说明不超宽、无 infinite、体积、以及**这一帧的图有没有变**（只移光圈/只换字会报 frame-static / frame-empty）。
- **reading.mjs**：只把每帧标题/说明/事实行导出成文字稿，给 reviewer 读；它不做质量判断。
- 脚本全绿不等于讲清楚。真正的验收是：reviewer 按帧复述能懂 + 主代理看图形是不是针对这一步（不是模板）。

## 卡片验收

| 门 | 判据 |
|---|---|
| 一卡一步 | 一个符号只被一张卡锚定；anchors 只写本步的 at，不挂相邻步骤/相邻函数（否则同一处会叠出多张卡） |
| 不套模板 | 任意两张卡结构不同；同一流程至少 3 种图形结构；连续两张像同一个模板 → 打回重做 |
| 一帧一点 | 每帧只讲一个极小知识点；出现“并且/同时/然后”就拆帧；帧数不设上限 |
| 每帧改图 | 每帧至少改一个图形元素（增/移/合/分/变色/计数/显隐）；只移光圈或只换字 → 打回 |
| 可读 | 完整、自然、说人话；术语先定义；**不设句数/字数上限**（3–5 句也可以）；图里只放名字和数字 |
| 术语顺序 | 先定义（大白话 + 术语）、再为什么、再机制；机制里的新术语用“大白话（术语）”指代，不递归 |
| 动作准确 | 设置/检查/复制/删除/读取不能混；页面标题与 card.yaml 一致 |
| 不自动播放 | radio + label 的 stepper，读者点一步看一步；无 infinite 动画 |
| 不叠 | 文字不压字、不压框、光圈不切字；qa 0 problems |
| 新人看懂 | 审查子代理按帧复述，说“看懂了”，没有“这里我不确定” |

## 流程验收

- 每步一个函数/方法；文件级只允许入口脚本、配置、模块 hub（后面必须跟同文件函数步）。
- 相邻步 6 跳内可达，或 via_relation 覆盖。
- 文本 20–60 字，有主语和动作，写“这一步之后什么变了”。
- 每一步都有 card；card_ok 全 true；无 broken/stale。

## 常见失败

| 失败 | 症状 | 改法 |
|---|---|---|
| 套模板 | 每张卡都是“输入 → 几个框 → 输出”，只是换字 | 打回，让 builder 按这一步的真实数据流重画 |
| 主代理自己写卡 | 主代理开始生成 SVG/HTML | 停，改派 builder |
| 把候选当流程 | 推荐时就把流程建了 | 等用户点 |
| 压句子 | 字少了但缺主语、指代不明 | 拆帧，不缩句 |
| 先用后定义 | 读者不知道 core dump 是什么就先说关掉它 | 按“是什么 → 为什么 → 怎么做到”重写，可拆 2–3 帧 |
| 一个 builder 做多步 | 后面几步开始套模板 | 一步一个 builder，全部并行派 |

## 文件

- [references/routes.md](references/routes.md)：怎么推荐路线、把流程拆到函数、连通与挂卡。
- [references/builder.md](references/builder.md)：制卡子代理的完整提示词（预算无上限、一帧一点、不套模板）。
- [references/reviewer.md](references/reviewer.md)：新人审查提示词与循环。
- **scripts/qa.mjs**：逐帧几何/可读性检查。
- **scripts/reading.mjs**：把卡导出成文字稿，给 reviewer 读。