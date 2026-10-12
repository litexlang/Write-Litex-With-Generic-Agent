#!/usr/bin/env python3
"""
Litex Error Parser - 即开即用的错误提取工具
从 litex_verified.json 递归提取完整的错误链

Usage:
    python3 parse_litex_error.py <litex_verified.json>
    
Example:
    python3 parse_litex_error.py solutions/problem_5/litex_verified.json

Output:
    - 验证状态（成功/失败）
    - 错误类型和行号
    - 失败的目标
    - 递归提取的完整错误链
    - 未知结果类型
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def extract_previous_errors(err_obj: Dict[str, Any], depth: int = 1) -> List[str]:
    """
    递归提取所有 previous_error 层级的信息
    
    Args:
        err_obj: 错误对象
        depth: 当前递归深度
        
    Returns:
        错误信息列表
    """
    if "previous_error" not in err_obj:
        return []
    
    prev_errors = []
    prev = err_obj["previous_error"]
    
    # 提取这一层的信息
    if "message" in prev:
        prefix = "详细原因" if depth == 1 else f"原因{depth}"
        prev_errors.append(f"\n{prefix}: {prev['message']}")
    
    if "failed_goal" in prev and "failed_goal" not in err_obj:
        prev_errors.append(f"\n失败的目标:\n{prev['failed_goal']}")
    
    if "unknown_result" in prev:
        unknown_prev = prev["unknown_result"]
        if isinstance(unknown_prev, dict):
            if "type" in unknown_prev:
                prev_errors.append(f"\n原因类型: {unknown_prev['type']}")
            if "goal" in unknown_prev:
                prev_errors.append(f"\n未知目标: {unknown_prev['goal']}")
    
    # 递归提取更深层
    prev_errors.extend(extract_previous_errors(prev, depth + 1))
    return prev_errors


def format_rollback_error(event: Dict[str, Any]) -> str:
    """
    从 litex 验证结果提取可读错误报告
    
    Args:
        event: litex 验证结果的 JSON 对象
        
    Returns:
        格式化的错误报告
    """
    parts: List[str] = ["❌ 验证失败"]
    
    # 处理 statement_results 结构
    for stmt in event.get("statement_results") or []:
        result = stmt.get("result") or {}
        execution = result.get("execution") or {}
        
        # 提取错误对象
        err = execution.get("error") or event.get("error") or {}
        
        if isinstance(err, dict):
            # 基本错误信息
            msg = err.get("message") or err.get("msg") or ""
            kind = err.get("kind") or err.get("error_type") or "error"
            line = err.get("line", "?")
            
            if msg:
                parts.append(f"\n({kind}, 行 {line}):\n{msg}")
            
            if "statement" in err:
                parts.append(f"\n失败的语句:\n{err['statement']}")
            
            if "failed_goal" in err:
                parts.append(f"\n失败的目标:\n{err['failed_goal']}")
            
            # 未知结果信息
            unknown = err.get("unknown_result") or {}
            if isinstance(unknown, dict):
                if "type" in unknown:
                    parts.append(f"\n原因类型: {unknown['type']}")
                if "goal" in unknown:
                    parts.append(f"\n未知目标: {unknown['goal']}")
            
            # 递归提取所有 previous_error
            parts.extend(extract_previous_errors(err))
        
        # 兼容 result 顶层直接带 failed_goal 的情况
        if "failed_goal" in result and "failed_goal" not in (err or {}):
            parts.append(f"\n失败的目标:\n{result['failed_goal']}")
    
    # 如果没有提取到任何有用信息，输出原始 error
    if len(parts) == 1 and event.get("error"):
        parts.append(f"\nerror: {json.dumps(event['error'], ensure_ascii=False)[:800]}")
    
    # 如果还是没有信息，输出完整 event 的前 1200 字符
    if len(parts) == 1:
        parts.append(f"\n完整输出:\n{json.dumps(event, ensure_ascii=False, indent=2)[:1200]}")
    
    return "".join(parts)


def is_success(event: Dict[str, Any]) -> bool:
    """
    判断验证是否成功
    
    Args:
        event: litex 验证结果的 JSON 对象
        
    Returns:
        True 如果验证成功，False 如果失败
    """
    # 检查顶层 ok 字段
    if event.get("ok") is False:
        return False
    
    # 检查 statement_results
    results = event.get("statement_results") or []
    if not results:
        return bool(event.get("ok"))
    
    for stmt in results:
        result = stmt.get("result") or {}
        execution = result.get("execution") or {}
        kind = execution.get("kind")
        
        # RolledBack 表示失败
        if kind == "RolledBack":
            return False
        
        # 检查错误标记
        if stmt.get("outcome") == "error" or result.get("kind") == "error":
            return False
    
    return True


def parse_litex_output(json_path: str) -> None:
    """
    解析 litex 验证输出并打印格式化报告
    
    Args:
        json_path: litex_verified.json 文件路径
    """
    path = Path(json_path)
    
    if not path.exists():
        print(f"❌ 错误：文件不存在: {json_path}")
        sys.exit(1)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
            # 处理空文件
            if not content:
                print("❌ 错误：文件为空")
                sys.exit(1)
            
            # 尝试解析 JSON
            data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ 错误：无效的 JSON 文件")
        print(f"详细信息: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误：读取文件失败")
        print(f"详细信息: {e}")
        sys.exit(1)
    
    # 判断是否成功
    success = is_success(data)
    
    print("=" * 60)
    if success:
        print("✅ 验证成功！")
        print("=" * 60)
        
        # 输出一些基本统计信息
        stmt_results = data.get("statement_results") or []
        if stmt_results:
            print(f"\n已验证 {len(stmt_results)} 个语句")
    else:
        print("❌ 验证失败")
        print("=" * 60)
        
        # 输出详细错误报告
        error_report = format_rollback_error(data)
        print(error_report)
    
    print("\n" + "=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_litex_error.py <litex_verified.json>")
        print("\nExample:")
        print("  python3 parse_litex_error.py solutions/problem_5/litex_verified.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    parse_litex_output(json_path)


if __name__ == "__main__":
    main()
