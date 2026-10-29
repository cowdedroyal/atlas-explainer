# 制卡子代理提示词（填空后整段发给 subagent）

> 你是这条流程里 **{n} 个并行 builder 之一**，只做这一步：**{step_at}**。
> 不要看别的卡、不要等别人；预算无上限，不要为了省帧数合并知识点。

## 工作方式（PTC）

用 **PTC / run_code 模式**：把“读代码、生成、跑 QA”写成程序批量执行，不要一条条手工调用工具。
每写完一张卡就跑一次 QA，绿了再下一张；不要攒到最后。

## 这一步在流程里的位置

- 上一步：{prev_step}
- 这一步：{step_at} — {step_text}
- 下一步：{next_step}

第一帧接上一步的结论；最后一帧点一句“下一步会看到什么”，不要展开下一步。

## 先读代码

~~~bash
codeatlas show "{step_at}" --code -r {repo}
~~~

- 以代码为准，不要只信步骤文字；把这一步涉及的调用方、被调方、shape、配置默认值都读到。
- 把这一步拆成 3–8 个“动作/状态变化”；每个动作一帧，复杂动作再拆。

## 核心要求（逐条遵守）

1. **每个问题用动画解释**，不靠长文。
2. **一帧只讲一个很小、很明确的知识点**；复杂点拆小。
3. **不要自动播放**：radio + label 的 stepper，读者点一步看一步。
4. **动画要细**：帧数不设上限，20–60 帧很正常；宁可多帧，不要合帧。
5. **图必须从这一步的真实结构长出来**：形状、流向、分支、计数、残影、对比。
   **不许套“输入 → 几个框 → 输出”的模板**；连续两张卡结构一样，就是没读代码。
   **也不许写一个通用生成器批量套所有卡**：每张卡单独设计版式。
6. **每一帧都要改图**：新增/移动/合并/分裂/变色/计数/显隐，至少改一个图形元素；
   **不能只移动光圈、只换 caption**。
7. **文字完整、自然**：先把术语和机制讲清楚，3–5 句也可以；不设句数/字数上限，不要为了短省主语、省为什么。
8. **图里只放名字和数字**，不放句子；不许文字压字、压框、光圈切字。
9. **卡片要好看**：留白、对齐、层级清楚，不要堆。
10. **不要编数字**：每个数字能指到代码行。
11. 写完自己以新人视角读一遍，再跑 QA。

## 最小 stepper 骨架（可以改样式，不要改成自动播放）

~~~html
<figure class="stepper" id="c1">
  <input class="st" type="radio" name="c1" id="c1-s1" checked>
  <input class="st" type="radio" name="c1" id="c1-s2">
  <div class="stage"><svg viewBox="0 0 900 520">…底图 + 每帧 <g class="fr fr1">…</g></svg></div>
  <div class="bar"><div class="ns ns1"><span class="nav off">上一步</span><label class="nav" for="c1-s2">下一步</label></div>…</div>
  <div class="caps"><div class="cap c1"><b>标题</b><span>一句说明</span></div>…</div>
</figure>
<script src="atlas-kit:1.js"></script>
~~~

~~~css
.st{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.fr{display:none}
#c1-s2:checked~.stage .fr2{display:inline}
#c1-s2:checked~.bar .ns2{display:flex}
#c1-s2:checked~.caps .c2{display:block}
~~~

尺寸和版式可以按这一步的内容改；但**必须**是“点一下换一帧”，不能有 infinite 动画。
只允许一次性过渡（例如光圈 0.4s pop）。

## 讲解文法：先术语，再为什么，再机制

每遇到一个术语或一个选择，按这三步写（可以跨 2–3 帧）：

1. **是什么**：一句大白话 + 术语（英文/符号）。
   例：core dump 是程序崩溃时把内存内容写成的一个文件（core dump）。
2. **为什么**：在这条流程里为什么需要它、为什么这样选。
   例：训练进程占几十 GB 内存，崩一次写 core 可能把磁盘撑满。
3. **怎么做到**：命令/机制；机制里冒出的新术语用“大白话（术语）”指代，不递归展开。
   例：ulimit -c 0 把 core 文件的大小上限设成 0（ulimit 是 shell 的资源上限开关）。

规则：

- 不许先用后定义。
- 不许只写“做了什么”，不写“为什么”。
- 机制里出现新术语，最多用括号给一个指代，不再展开；它是后面的主角就留到那一步。
- 一段话里出现两个没解释的新词，说明这一帧该拆。
- **动词要准确**：先看代码是读还是写；“设置/检查/复制/删除/读取”不能混。
  例：`ulimit -c 0` 是设置上限；`ulimit -c`（不带值）才是读取；`if [ -f ... ]` 才是检查文件存在。
- **事实行只补充行号/公式，不是把机制挪出 caption 的地方**；caption 要能单独讲清。

反例 / 正例：

| 反例 | 正例（照这个讲） |
|---|---|
| “关掉 core dump。程序崩溃时不再写出 core 文件。” | “Core dump（核心转储）是程序崩溃时，操作系统把程序当时的完整内存快照写入磁盘的一个文件。不过在当前项目中训练进程可能几十 GB，多写几次可能会撑满磁盘。为了防止这种情况，ulimit -c 0 指的是把存储上限设成 0。脚本没有先读当前值，直接用 ulimit -c 0 把 core 文件上限设成 0——是设置，不是检查” |

## 每写一帧，问自己

- 这一帧只加了哪一个事实？上一帧读者已经知道什么？
- 把图遮住，只读标题和说明，能复述吗？
- 这个数字/公式来自代码哪一行？
- 这个术语第一次出现定义了吗？
- 光圈有没有切到字？文字有没有和图抢位置？
- 如果我是新人，会在这一帧停下来问什么？下一帧回答了吗？

写完整张再问一次：如果我是新人，会在哪一帧掉队？那一帧就是下一轮要拆或要补的。

## 产出

- 目录：{out_dir}/{card_id}/
- card.yaml：kit: 1、id、title、questions、summary、anchors（**只写 {anchors} 这一个，不要加相邻函数或相邻步骤的符号**）、tags、language: zh
- index.html：自包含的 stepper；引用 atlas-kit:1.css / atlas-kit:1.js；无自定义脚本、无事件属性。
- index.html 的 `<title>` 和页面大标题必须与 card.yaml 的 title **完全一致**；不要另起第三个标题。
- 不要改 tour、不要 apply、不要碰别人的卡。

## 自检

~~~bash
node {skill}/scripts/qa.mjs {out_dir}/{card_id}/index.html light 900
~~~

要求 ok=true、problemCount=0、无 infinite。再截一张图，自己看一眼：有没有文字压图、留白够不够、每帧的图是不是真的在变。然后逐帧看一遍文字稿：

~~~bash
node {skill}/scripts/reading.mjs {out_dir}/{card_id}/index.html
~~~

## 完成后：自己开 reviewer 审（最多 2 轮）

用 **subagent（全新上下文，不要 fork）**，按 [reviewer.md](reviewer.md) 审你这张卡。
reviewer 只审“你看不懂”的阻塞点；你只修阻塞条目，排版/措辞/“可以更好”记下来，不改。
最多 2 轮 reviewer（2 个会话）；第 2 轮后不管它还能挑出什么，都停，汇报。
不要为了讨好 reviewer 无限加帧或反复改版式；也不要每轮新开一串 reviewer。
如果环境不能开子代理，在汇报里说明。

## 汇报

帧数 / 每帧一句话 / qa 结果 / 还不确定的事实（0–3 条）。