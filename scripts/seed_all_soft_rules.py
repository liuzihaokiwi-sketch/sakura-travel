#!/usr/bin/env python3
"""
批量运行所有软规则系统 seed 脚本
包含: B1, B5, B6, B7, B8 任务
用法: python scripts/seed_all_soft_rules.py [--dry-run] [--skip-json]
"""

from __future__ import annotations

import asyncio
import logging
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import argparse

# ── 路径修复 ──────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── Seed 脚本配置 ──────────────────────────────────────────────────────────────
SEED_SCRIPTS = [
    {
        "id": "B1",
        "name": "product_config 种子数据",
        "script": "seed_product_config.py",
        "description": "写入3个SKU配置到product_config表",
        "dependencies": []
    },
    {
        "id": "B5",
        "name": "软规则维度定义",
        "script": None,  # 这是Python模块，不是脚本
        "module": "app.domains.scoring.soft_rule_dimensions",
        "description": "创建12维软规则维度定义文件",
        "dependencies": []
    },
    {
        "id": "B6",
        "name": "软规则默认权重JSON",
        "script": "seed_soft_rule_defaults.py",
        "description": "创建软规则默认权重JSON文件",
        "dependencies": ["B5"]
    },
    {
        "id": "B7",
        "name": "客群权重包",
        "script": "seed_segment_weight_packs.py",
        "description": "写入7个客群权重包到segment_weight_packs表",
        "dependencies": ["B5", "B6"]
    },
    {
        "id": "B8",
        "name": "阶段权重包",
        "script": "seed_stage_weight_packs.py",
        "description": "写入4个阶段权重包到stage_weight_packs表",
        "dependencies": ["B5", "B6"]
    }
]


def run_script(script_path: str, dry_run: bool = False) -> bool:
    """运行Python脚本"""
    try:
        cmd = [sys.executable, script_path]
        if dry_run:
            cmd.append("--dry-run")
        
        logger.info(f"运行脚本: {script_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            logger.info(f"脚本执行成功: {script_path}")
            if result.stdout:
                logger.debug(f"输出:\n{result.stdout}")
            return True
        else:
            logger.error(f"脚本执行失败: {script_path}")
            logger.error(f"错误输出:\n{result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"运行脚本时出错 {script_path}: {e}")
        return False


def test_module_import(module_path: str) -> bool:
    """测试Python模块导入"""
    try:
        logger.info(f"测试模块导入: {module_path}")
        __import__(module_path)
        logger.info(f"模块导入成功: {module_path}")
        return True
    except ImportError as e:
        logger.error(f"模块导入失败 {module_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"测试模块时出错 {module_path}: {e}")
        return False


async def run_seed_scripts(dry_run: bool = False, skip_json: bool = False) -> Dict[str, Any]:
    """运行所有seed脚本"""
    results = {}
    scripts_dir = Path(__file__).parent
    
    print("\n" + "="*70)
    print("软规则系统 Seed 脚本批量执行")
    print("="*70)
    
    for script_config in SEED_SCRIPTS:
        script_id = script_config["id"]
        script_name = script_config["name"]
        
        print(f"\n[{script_id}] {script_name}")
        print(f"  描述: {script_config['description']}")
        
        # 检查依赖
        deps = script_config.get("dependencies", [])
        if deps:
            missing_deps = [dep for dep in deps if dep not in results or not results[dep].get("success")]
            if missing_deps:
                logger.warning(f"  跳过: 依赖未完成: {missing_deps}")
                results[script_id] = {
                    "success": False,
                    "skipped": True,
                    "reason": f"依赖未完成: {missing_deps}"
                }
                continue
        
        # 特殊处理B5（模块导入测试）
        if script_id == "B5":
            success = test_module_import(script_config["module"])
            results[script_id] = {
                "success": success,
                "type": "module_import"
            }
        
        # 特殊处理B6（JSON文件生成，可选跳过）
        elif script_id == "B6" and skip_json:
            logger.info("  跳过JSON文件生成 (--skip-json)")
            results[script_id] = {
                "success": True,
                "skipped": True,
                "reason": "用户选择跳过JSON生成"
            }
        
        # 运行Python脚本
        elif script_config["script"]:
            script_path = scripts_dir / script_config["script"]
            if not script_path.exists():
                logger.error(f"  脚本不存在: {script_path}")
                results[script_id] = {
                    "success": False,
                    "error": f"脚本不存在: {script_path}"
                }
                continue
            
            success = run_script(str(script_path), dry_run)
            results[script_id] = {
                "success": success,
                "script": script_config["script"]
            }
        
        else:
            logger.error(f"  无效的脚本配置: {script_config}")
            results[script_id] = {
                "success": False,
                "error": "无效的脚本配置"
            }
    
    return results


def print_summary(results: Dict[str, Any], dry_run: bool = False) -> None:
    """打印执行摘要"""
    print("\n" + "="*70)
    print("执行摘要")
    print("="*70)
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for script_id, result in results.items():
        script_config = next(s for s in SEED_SCRIPTS if s["id"] == script_id)
        script_name = script_config["name"]
        
        if result.get("skipped"):
            status = "🟡 跳过"
            skip_count += 1
            reason = result.get("reason", "未知原因")
            print(f"{script_id:4} {script_name:20} {status:10} ({reason})")
        elif result.get("success"):
            status = "✅ 成功"
            success_count += 1
            print(f"{script_id:4} {script_name:20} {status:10}")
        else:
            status = "❌ 失败"
            fail_count += 1
            error = result.get("error", "未知错误")
            print(f"{script_id:4} {script_name:20} {status:10} ({error})")
    
    print("\n" + "="*70)
    print("统计结果")
    print("="*70)
    
    total = len(results)
    print(f"总计: {total} 个任务")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"跳过: {skip_count}")
    
    if dry_run:
        print("\n⚠️  Dry run 模式: 未实际写入数据库")
    
    if fail_count == 0:
        print("\n🎉 所有任务执行完成!")
        
        if not dry_run:
            print("\n下一步建议:")
            print("1. 运行数据库迁移: alembic upgrade head")
            print("2. 测试软规则计算功能")
            print("3. 继续 Wave 0 的其他任务 (C1-C5, D1-D5, E1-E7)")
    else:
        print(f"\n⚠️  有 {fail_count} 个任务失败，请检查错误信息")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量运行软规则系统 seed 脚本")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不实际写入数据库")
    parser.add_argument("--skip-json", action="store_true", help="跳过JSON文件生成")
    parser.add_argument("--list", action="store_true", help="列出所有可用的seed脚本")
    
    args = parser.parse_args()
    
    if args.list:
        print("软规则系统 Seed 脚本清单:")
        print("="*50)
        for script in SEED_SCRIPTS:
            print(f"\n{script['id']}: {script['name']}")
            print(f"  描述: {script['description']}")
            if script.get('dependencies'):
                print(f"  依赖: {', '.join(script['dependencies'])}")
            if script.get('script'):
                print(f"  脚本: {script['script']}")
            elif script.get('module'):
                print(f"  模块: {script['module']}")
        return
    
    # 运行seed脚本
    results = asyncio.run(run_seed_scripts(dry_run=args.dry_run, skip_json=args.skip_json))
    
    # 打印摘要
    print_summary(results, dry_run=args.dry_run)


if __name__ == "__main__":
    main()