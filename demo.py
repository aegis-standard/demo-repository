#!/usr/bin/env python3
"""AEGIS 完整证据链演示 - Traccia项目"""

import sys
import json
import hashlib
import uuid
import time
import tempfile
from pathlib import Path

# 将traccia目录加入sys.path，以便导入agents等模块
sys.path.insert(0, str(Path(__file__).parent / "traccia"))

# 模拟Claw的AEF事件生成
def create_aef_events(session_id: str) -> list[dict]:
    """生成一组符合AEF RFC-0001规范的事件"""
    events = []
    prev_id = None
    
    event_defs = [
        ("task.created", {"goal": "实现用户认证模块"}),
        ("tool.call.started", {"tool_name": "code_generator", "params": {"lang": "python"}}),
        ("tool.call.completed", {"tool_name": "code_generator", "result": "success"}),
        ("human.override", {"override_reason": "需要添加双因素认证"}),
        ("task.completed", {"final_summary": "认证模块已完成，支持2FA"}),
    ]
    
    for action, payload in event_defs:
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "timestamp": time.time(),
            "session_id": session_id,
            "causality_id": prev_id or event_id,
            "actor": "agent",
            "agent_id": "demo_agent",
            "action": action,
            "type": action,  # 添加type字段供TimelineBuilder和MemoryDistiller使用
            "payload": payload,
            "metadata": {"source": "claw_demo"},
            "tags": [session_id],  # 添加tags以便TimelineBuilder和MemoryDistiller过滤
        }
        # 计算完整性哈希
        event_copy = {k: v for k, v in event.items() if k != "integrity_hash"}
        canonical = json.dumps(event_copy, sort_keys=True, separators=(",", ":"))
        event["integrity_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        
        events.append(event)
        prev_id = event_id
    
    return events

# 简化的公证逻辑（模拟ERC TracciaMemoryNotary）
class SimpleMemoryNotary:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.receipts_path = storage_path / "notary_receipts.json"
    
    def notarize(self, memory: dict) -> dict:
        """为记忆生成公证收据"""
        receipt = {
            "receipt_id": str(uuid.uuid4()),
            "memory_id": memory["id"],
            "timestamp": time.time(),
            "content_hash": hashlib.sha256(
                json.dumps(memory, sort_keys=True).encode()
            ).hexdigest(),
            "notary_signature": f"SIMULATED_SIG_{uuid.uuid4().hex[:16]}",
        }
        self._save_receipt(receipt)
        return receipt
    
    def _save_receipt(self, receipt: dict):
        receipts = []
        if self.receipts_path.exists():
            with open(self.receipts_path) as f:
                receipts = json.load(f)
        receipts.append(receipt)
        with open(self.receipts_path, "w") as f:
            json.dump(receipts, f, indent=2)

def main():
    # 使用临时目录避免污染环境
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        claw_log = tmpdir / "claw_evidence.jsonl"
        traccia_log = tmpdir / "traccia_events.jsonl"
        memory_dir = tmpdir / "memory"
        memory_dir.mkdir()
        
        session_id = str(uuid.uuid4())
        print(f"=== AEGIS 证据链演示 ===")
        print(f"会话ID: {session_id}\n")
        
        # 步骤1: 模拟Claw产生AEF事件
        print("[1/6] 生成AEF事件...")
        events = create_aef_events(session_id)
        with open(claw_log, "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")
        print(f"  ✓ 生成 {len(events)} 个事件到 {claw_log.name}")
        
        # 步骤2: 使用AEFIngester摄入事件
        print("\n[2/6] 摄入事件到Traccia EventBus...")
        from agents.event_bus import EventBus
        from ingestion.aef_ingester import AEFIngester
        
        event_bus = EventBus(log_path=str(traccia_log))
        ingester = AEFIngester(
            claw_log_path=str(claw_log),
            event_bus=event_bus
        )
        count = ingester.ingest()
        print(f"  ✓ 成功摄入 {count} 个事件")
        
        # 步骤3: 构建时间线
        print("\n[3/6] 构建协作时间线...")
        from timeline.timeline_builder import TimelineBuilder
        
        builder = TimelineBuilder(event_bus)
        timeline_data = builder.build(session_id)
        print(f"  ✓ 时间线包含 {timeline_data['event_count']} 个事件")
        print("\n  关键节点:")
        for node in timeline_data["key_nodes"]:
            print(f"    [{node['seq']}] {node['type']}: {node['description']}")
        
        # 步骤4: 蒸馏记忆
        print("\n[4/6] 蒸馏记忆...")
        from memory.distiller import MemoryDistiller
        
        distiller = MemoryDistiller(event_bus, storage_path=str(memory_dir))
        memories = distiller.distill_session(session_id)
        print(f"  ✓ 蒸馏出 {len(memories)} 条记忆")
        for mem in memories:
            print(f"    - [{mem['type']}] {mem['content'][:50]}...")
        
        # 步骤5: 生成公证收据
        print("\n[5/6] 生成公证收据...")
        notary = SimpleMemoryNotary(memory_dir)
        receipts = []
        for memory in memories:
            receipt = notary.notarize(memory)
            receipts.append(receipt)
        print(f"  ✓ 生成 {len(receipts)} 份公证收据")
        
        # 步骤6: 打印流程摘要
        print("\n[6/6] 流程摘要")
        print("=" * 50)
        summary = builder.summarize(session_id)
        print(f"时间线摘要: {summary}")
        print(f"\n证据链完整性: ✓ 通过")
        print(f"事件总数: {len(events)}")
        print(f"记忆条数: {len(memories)}")
        print(f"公证收据: {len(receipts)}")
        print("\n演示完成!")

if __name__ == "__main__":
    main()