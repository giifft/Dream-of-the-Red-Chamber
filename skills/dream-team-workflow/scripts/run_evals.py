#!/usr/bin/env python3
import json
import os
import sys

# 将当前脚本所在目录加入到 sys.path，以便导入 route_workflow
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from route_workflow import route_workflow, WorkflowType

def run_tests():
    # 确定 evals.json 路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    evals_path = os.path.join(base_dir, "evals", "evals.json")
    
    if not os.path.exists(evals_path):
        print(f"Error: evals.json not found at {evals_path}")
        sys.exit(1)
        
    with open(evals_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    evals = data.get("evals", [])
    print(f"Loaded {len(evals)} evaluation cases.")
    
    # 映射 json 中的 workflow_type 名字到 WorkflowType 常量
    type_mapping = {
        "快速模式": WorkflowType.QUICK,
        "BugFix": WorkflowType.BUGFIX,
        "敏捷战队(AI-RAG)": WorkflowType.AGILE_AI,
        "敏捷战队(AI)": WorkflowType.AGILE_AI,
        "敏捷战队(算法建模)": WorkflowType.AGILE_ML,
        "敏捷战队(安全加固)": WorkflowType.AGILE_SEC,
        "AI-Agent 战队": WorkflowType.AGILE_AGENT,
        "MCP Server 战队": WorkflowType.AGILE_MCP,
        "标准SOP": WorkflowType.STANDARD,
        "标准SOP+AI+安全": WorkflowType.STANDARD,
        "LLMOps": WorkflowType.LLMOPS,
    }
    
    passed = 0
    failed = 0
    
    for case in evals:
        prompt = case.get("prompt")
        expected_zh = case.get("workflow_type")
        expected_type = type_mapping.get(expected_zh)
        
        # 运行路由
        actual_type, description, roles = route_workflow(prompt)
        
        # 判断分类是否正确
        is_match = False
        if expected_type == actual_type:
            is_match = True
        elif expected_zh == "标准SOP+AI+安全" and actual_type == WorkflowType.STANDARD:
            is_match = True
            
        if is_match:
            print(f" [PASS] Case #{case.get('id')}: '{prompt[:25]}...' -> Expected: {expected_zh}, Actual: {actual_type}")
            passed += 1
        else:
            print(f"❌ [FAIL] Case #{case.get('id')}: '{prompt[:25]}...' -> Expected: {expected_zh} ({expected_type}), Actual: {actual_type}")
            failed += 1
            
    print(f"\nTest Summary: {passed} passed, {failed} failed.")
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
