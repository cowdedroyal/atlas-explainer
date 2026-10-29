# 路线与流程

## 推荐路线（粗）

先回答，再从问题反推 3–5 条用户可能不熟的路线。每条一行：**名字 / 入口 / 出口 / 2–4 个关键步**。

| 用户问的 | 可能不熟的路线 |
|---|---|
| shape / 维度 / 通道 | 数据流过模型：输入 → backbone → 池化/拼接 → token |
| 指标 / 数值 | 训练 → 评测 → 指标计算 |
| 某个文件 / 函数 | 它所在的调用链：入口 → … → 效果 |
| 配置 / 启动 | 脚本 → config → Trainer |
| 数据 / 标签 | 数据构建，或训练时在线加载 |
| 报错 / loss 不降 | 训练循环，或失败路径 |

推荐可以粗；只有用户点了的那条才建，建的时候必须细。

## 建流程

~~~bash
codeatlas outline -r <repo>
codeatlas agenda --type tour -r <repo>
codeatlas tours -r <repo>
codeatlas path A B -r <repo>
codeatlas validate -f tour.json -r <repo>
codeatlas apply -f tour.json -r <repo>
~~~

- 一步一个函数/方法；文件级只允许入口脚本、配置、模块 hub（hub 后面必须跟同文件函数步）。
- 文本 20–60 字，写“这一步之后什么变了”；不写参数表、不写调用栈。
- 相邻步 6 跳内可达；跨边界用 via_relation。
- 一步挂一张卡：step 里写 card: <id>；卡的 anchors **只写这一步的 at**，不要挂相邻步骤的函数、也不要挂相邻函数（否则同一个代码位置会冒出好几张卡，读者分不清）。
- 一条流程 8–18 步；超过就再拆一条。

## 挂卡与检查

~~~bash
codeatlas card apply <card-dir> -r <repo>
codeatlas tours -r <repo>        # card / card_ok / state
~~~

card_ok 全 true、state 无 broken，才算流程完成。