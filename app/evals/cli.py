"""
Eval CLI — 评测命令行工具 (E7)

用法：
  python -m app.evals.cli run --suite regression
  python -m app.evals.cli run --case C001
  python -m app.evals.cli run --all
  python -m app.evals.cli compare <run-id-a> <run-id-b>
  python -m app.evals.cli list-cases [--suite standard]
  python -m app.evals.cli show <run-id>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── 懒加载，避免冷启动慢 ──────────────────────────────────────────────────────

def _get_engine():
    from app.evals.engine import EvalEngine
    return EvalEngine()


CASES_DIR = Path("evals/cases")
RUNS_DIR = Path("evals/runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)


# ── 子命令：run ───────────────────────────────────────────────────────────────

async def cmd_run(args: argparse.Namespace) -> int:
    engine = _get_engine()

    if args.case:
        case_file = _find_case_file(args.case)
        if not case_file:
            print(f"❌ 未找到用例: {args.case}", file=sys.stderr)
            return 1
        results = [await engine.run_case_from_file(str(case_file))]
        run_name = f"single-{args.case}-{_ts()}"

    elif args.suite:
        suite_dir = CASES_DIR / args.suite
        if not suite_dir.exists():
            print(f"❌ 测试套件目录不存在: {suite_dir}", file=sys.stderr)
            return 1
        case_files = list(suite_dir.glob("*.yaml")) + list(suite_dir.glob("*.yml"))
        if not case_files:
            print(f"⚠️  套件 {args.suite} 下没有用例文件", file=sys.stderr)
            return 0
        results = []
        for cf in sorted(case_files):
            print(f"  运行: {cf.stem} ...", end="", flush=True)
            try:
                r = await engine.run_case_from_file(str(cf))
                results.append(r)
                verdict = "✅ PASS" if r.get("passed") else "❌ FAIL"
                print(f" {verdict} ({r.get('composite_score', 0):.0f}/100)")
            except Exception as e:
                print(f" 💥 ERROR: {e}")
        run_name = f"{args.suite}-{_ts()}"

    elif args.all:
        results = []
        for case_file in sorted(CASES_DIR.rglob("*.yaml")):
            print(f"  运行: {case_file.stem} ...", end="", flush=True)
            try:
                r = await engine.run_case_from_file(str(case_file))
                results.append(r)
                verdict = "✅" if r.get("passed") else "❌"
                print(f" {verdict}")
            except Exception as e:
                print(f" 💥 {e}")
        run_name = f"all-{_ts()}"
    else:
        print("❌ 请指定 --case / --suite / --all", file=sys.stderr)
        return 1

    # 持久化运行结果
    run_file = RUNS_DIR / f"{run_name}.json"
    summary = _build_summary(run_name, results)
    run_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # 输出报告
    _print_report(summary, args.format)

    return 0 if summary["failed"] == 0 else 1


# ── 子命令：compare ───────────────────────────────────────────────────────────

def cmd_compare(args: argparse.Namespace) -> int:
    run_a_file = RUNS_DIR / f"{args.run_a}.json"
    run_b_file = RUNS_DIR / f"{args.run_b}.json"

    for f in [run_a_file, run_b_file]:
        if not f.exists():
            print(f"❌ 找不到运行文件: {f}", file=sys.stderr)
            return 1

    run_a = json.loads(run_a_file.read_text())
    run_b = json.loads(run_b_file.read_text())

    print(f"\n## 评测运行对比\n")
    print(f"| 指标 | {args.run_a} | {args.run_b} | 变化 |")
    print(f"|------|------------|------------|------|")

    metrics = [
        ("总用例", "total"),
        ("通过", "passed"),
        ("失败", "failed"),
        ("平均综合分", "avg_composite"),
        ("平均结构分", "avg_structure"),
        ("平均规划分", "avg_planning"),
        ("平均体验分", "avg_user_value"),
    ]
    for label, key in metrics:
        a_val = run_a.get(key, 0)
        b_val = run_b.get(key, 0)
        if isinstance(a_val, float):
            diff = b_val - a_val
            sign = "▲" if diff > 0 else ("▼" if diff < 0 else "—")
            print(f"| {label} | {a_val:.1f} | {b_val:.1f} | {sign}{abs(diff):.1f} |")
        else:
            diff = int(b_val) - int(a_val)
            sign = "▲" if diff > 0 else ("▼" if diff < 0 else "—")
            print(f"| {label} | {a_val} | {b_val} | {sign}{abs(diff)} |")

    # 找出 B 比 A 退步的用例
    a_by_case = {r["case_id"]: r for r in run_a.get("results", [])}
    b_by_case = {r["case_id"]: r for r in run_b.get("results", [])}
    regressions = []
    for case_id, b_res in b_by_case.items():
        a_res = a_by_case.get(case_id)
        if a_res and a_res.get("passed") and not b_res.get("passed"):
            regressions.append(case_id)

    if regressions:
        print(f"\n### ⚠️ 新增失败（回归）\n")
        for cid in regressions:
            print(f"  - {cid}")
    else:
        print(f"\n✅ 无新增失败")

    return 0


# ── 子命令：list-cases ────────────────────────────────────────────────────────

def cmd_list_cases(args: argparse.Namespace) -> int:
    if args.suite:
        dirs = [CASES_DIR / args.suite]
    else:
        dirs = [d for d in CASES_DIR.iterdir() if d.is_dir()]

    total = 0
    for d in sorted(dirs):
        files = list(d.glob("*.yaml")) + list(d.glob("*.yml"))
        if files:
            print(f"\n📁 {d.name} ({len(files)} 个用例)")
            for f in sorted(files):
                print(f"   - {f.stem}")
            total += len(files)
    print(f"\n共 {total} 个用例")
    return 0


# ── 子命令：show ──────────────────────────────────────────────────────────────

def cmd_show(args: argparse.Namespace) -> int:
    run_file = RUNS_DIR / f"{args.run_id}.json"
    if not run_file.exists():
        # 模糊匹配
        matches = list(RUNS_DIR.glob(f"*{args.run_id}*.json"))
        if not matches:
            print(f"❌ 找不到运行: {args.run_id}", file=sys.stderr)
            return 1
        run_file = matches[0]

    summary = json.loads(run_file.read_text())
    _print_report(summary, args.format if hasattr(args, "format") else "text")
    return 0


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def _find_case_file(case_id: str) -> Optional[Path]:
    for f in CASES_DIR.rglob("*.yaml"):
        if f.stem == case_id or f.stem.startswith(case_id):
            return f
    return None


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _build_summary(run_name: str, results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed
    scores = [r.get("composite_score", 0) for r in results if r.get("composite_score") is not None]
    struct_scores = [r.get("structure_score", 0) for r in results if r.get("structure_score") is not None]
    plan_scores = [r.get("planning_score", 0) for r in results if r.get("planning_score") is not None]
    uv_scores = [r.get("user_value_score", 0) for r in results if r.get("user_value_score") is not None]

    return {
        "run_name": run_name,
        "run_at": datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total * 100, 1) if total else 0,
        "avg_composite": round(sum(scores) / len(scores), 1) if scores else 0,
        "avg_structure": round(sum(struct_scores) / len(struct_scores), 1) if struct_scores else 0,
        "avg_planning": round(sum(plan_scores) / len(plan_scores), 1) if plan_scores else 0,
        "avg_user_value": round(sum(uv_scores) / len(uv_scores), 1) if uv_scores else 0,
        "results": results,
    }


def _print_report(summary: dict, fmt: str = "text") -> None:
    if fmt == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    # Markdown 格式
    print(f"\n## 评测报告：{summary['run_name']}")
    print(f"运行时间：{summary.get('run_at', '未知')}\n")
    print(f"| 指标 | 结果 |")
    print(f"|------|------|")
    print(f"| 总用例 | {summary['total']} |")
    print(f"| 通过 ✅ | {summary['passed']} ({summary.get('pass_rate', 0):.1f}%) |")
    print(f"| 失败 ❌ | {summary['failed']} |")
    print(f"| 平均综合分 | {summary.get('avg_composite', 0):.1f}/100 |")
    print(f"| 平均结构分 | {summary.get('avg_structure', 0):.1f}/100 |")
    print(f"| 平均规划分 | {summary.get('avg_planning', 0):.1f}/100 |")
    print(f"| 平均体验分 | {summary.get('avg_user_value', 0):.1f}/100 |")

    failed_cases = [r for r in summary.get("results", []) if not r.get("passed")]
    if failed_cases:
        print(f"\n### ❌ 失败用例\n")
        for r in failed_cases:
            print(f"- **{r['case_id']}**：{r.get('composite_score', 0):.0f}/100")
            for issue in (r.get("issues") or [])[:3]:
                print(f"  - {issue}")


# ── 入口 ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.evals.cli",
        description="Travel AI 评测飞轮 CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # run
    p_run = sub.add_parser("run", help="运行评测用例")
    p_run.add_argument("--case", help="指定单个用例 ID（如 C001）")
    p_run.add_argument("--suite", help="指定测试套件（standard/regression/...）")
    p_run.add_argument("--all", action="store_true", help="运行所有用例")
    p_run.add_argument("--format", choices=["text", "json"], default="text")

    # compare
    p_cmp = sub.add_parser("compare", help="对比两次运行结果")
    p_cmp.add_argument("run_a", help="基线运行 ID")
    p_cmp.add_argument("run_b", help="对比运行 ID")

    # list-cases
    p_list = sub.add_parser("list-cases", help="列出所有用例")
    p_list.add_argument("--suite", help="过滤套件")

    # show
    p_show = sub.add_parser("show", help="展示运行详情")
    p_show.add_argument("run_id", help="运行 ID 或关键字")
    p_show.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()

    if args.command == "run":
        return asyncio.run(cmd_run(args))
    elif args.command == "compare":
        return cmd_compare(args)
    elif args.command == "list-cases":
        return cmd_list_cases(args)
    elif args.command == "show":
        return cmd_show(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
