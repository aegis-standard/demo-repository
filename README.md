# AEGIS — AI 代理执行证据生态演示

本仓库演示 AEF (Agent Evidence Format) 生态系统的完整端到端闭环，从 AI 行为发生到法律级公证的全过程。

## 快速开始

```bash
python demo.py

演示流程
生成 AEF 事件（task.created → tool.call.* → human.override → task.completed）

将事件摄入到 Traccia EventBus 并验证完整性

构建协作时间线并标注关键决策点

蒸馏认知记忆（偏好 + 项目上下文）

生成 ERC 公证收据

AEGIS 生态仓库
项目	描述
AEF Core	执行证据格式宪法 + RFC
Claw Reference Runtime	可审计的本地 Agent 执行黑匣子
Traccia	认知时间线 + 记忆蒸馏
ERC	责任收据引擎
许可证
CC0 1.0 Universal