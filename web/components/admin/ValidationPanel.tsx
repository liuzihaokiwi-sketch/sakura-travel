"use client";

import { useState } from "react";

// ── 类型 ──────────────────────────────────────────────────────────────────────

export interface ValidationRuleResult {
  rule_id: string;
  color: "red" | "yellow" | "green";
  passed: boolean;
  message: string;
  follow_up?: string | null;
  field?: string | null;
}

export interface ValidationSummary {
  form_id: string;
  overall: "red" | "yellow" | "green";
  can_generate: boolean;
  red_count: number;
  yellow_count: number;
  results: ValidationRuleResult[];
  failed: ValidationRuleResult[];
  follow_ups: string[];
}

interface Props {
  summary: ValidationSummary;
  onCopyFollowUp?: (text: string) => void;
}

// ── 工具 ──────────────────────────────────────────────────────────────────────

const COLOR_CONFIG = {
  red:    { bg: "bg-red-50",    border: "border-red-200",    dot: "bg-red-500",    text: "text-red-700",    label: "🔴 必须追问" },
  yellow: { bg: "bg-amber-50",  border: "border-amber-200",  dot: "bg-amber-400",  text: "text-amber-700",  label: "🟡 建议补充" },
  green:  { bg: "bg-green-50",  border: "border-green-200",  dot: "bg-green-500",  text: "text-green-700",  label: "✅ 通过" },
};

function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).catch(() => {});
  } else {
    const el = document.createElement("textarea");
    el.value = text;
    el.style.position = "fixed";
    el.style.opacity = "0";
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
  }
}

// ── 单条规则行 ────────────────────────────────────────────────────────────────

function RuleRow({ r }: { r: ValidationRuleResult }) {
  const [copied, setCopied] = useState(false);
  const cfg = COLOR_CONFIG[r.color];

  const handleCopy = () => {
    if (r.follow_up) {
      copyText(r.follow_up);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={`flex items-start gap-3 px-4 py-3 rounded-lg border ${cfg.bg} ${cfg.border}`}>
      <span className={`mt-1 w-2.5 h-2.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <span className={`text-xs font-semibold ${cfg.text} mr-2`}>{cfg.label}</span>
            <span className="text-xs text-gray-400">{r.rule_id}</span>
            {r.field && (
              <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                {r.field}
              </span>
            )}
          </div>
          {!r.passed && r.follow_up && (
            <button
              onClick={handleCopy}
              className="flex-shrink-0 text-xs px-2 py-1 rounded bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              {copied ? "✓ 已复制" : "复制话术"}
            </button>
          )}
        </div>
        <p className="text-sm text-gray-700 mt-0.5">{r.message}</p>
        {!r.passed && r.follow_up && (
          <p className="text-xs text-gray-500 mt-1.5 bg-white/60 rounded px-2 py-1 border border-gray-100 italic">
            💬 {r.follow_up}
          </p>
        )}
      </div>
    </div>
  );
}

// ── 主组件 ────────────────────────────────────────────────────────────────────

export default function ValidationPanel({ summary, onCopyFollowUp }: Props) {
  const [showAll, setShowAll] = useState(false);
  const [allCopied, setAllCopied] = useState(false);

  const failedRed    = summary.results.filter((r) => !r.passed && r.color === "red");
  const failedYellow = summary.results.filter((r) => !r.passed && r.color === "yellow");
  const passed       = summary.results.filter((r) => r.passed);

  const allFollowUps = summary.follow_ups.filter(Boolean).join("\n\n");

  const handleCopyAll = () => {
    if (allFollowUps) {
      copyText(allFollowUps);
      onCopyFollowUp?.(allFollowUps);
      setAllCopied(true);
      setTimeout(() => setAllCopied(false), 2000);
    }
  };

  const overallCfg = COLOR_CONFIG[summary.overall];

  return (
    <div className="space-y-4">
      {/* 总览 header */}
      <div className={`flex items-center justify-between p-4 rounded-xl border ${overallCfg.bg} ${overallCfg.border}`}>
        <div className="flex items-center gap-3">
          <span className={`w-3 h-3 rounded-full ${overallCfg.dot}`} />
          <div>
            <p className={`font-semibold ${overallCfg.text}`}>
              {summary.overall === "green"
                ? "校验通过，可以生成"
                : summary.overall === "yellow"
                ? "建议追问后再生成"
                : "有必填项缺失，必须追问"}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              {summary.red_count > 0 && `${summary.red_count} 个必须追问 · `}
              {summary.yellow_count > 0 && `${summary.yellow_count} 个建议补充 · `}
              {passed.length} 个已通过
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {allFollowUps && (
            <button
              onClick={handleCopyAll}
              className="text-sm px-3 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors font-medium"
            >
              {allCopied ? "✓ 已复制全部话术" : "📋 复制所有追问话术"}
            </button>
          )}
          <span className={`text-sm font-bold px-3 py-1 rounded-lg ${
            summary.can_generate
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}>
            {summary.can_generate ? "可生成" : "待追问"}
          </span>
        </div>
      </div>

      {/* 🔴 必须追问 */}
      {failedRed.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-1">
            必须追问（{failedRed.length}）
          </h4>
          {failedRed.map((r) => <RuleRow key={r.rule_id} r={r} />)}
        </div>
      )}

      {/* 🟡 建议补充 */}
      {failedYellow.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-1">
            建议补充（{failedYellow.length}）
          </h4>
          {failedYellow.map((r) => <RuleRow key={r.rule_id} r={r} />)}
        </div>
      )}

      {/* ✅ 已通过（可折叠） */}
      {passed.length > 0 && (
        <div>
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors px-1"
          >
            {showAll ? "▲ 收起" : `▶ 查看 ${passed.length} 个通过项`}
          </button>
          {showAll && (
            <div className="space-y-1.5 mt-2">
              {passed.map((r) => <RuleRow key={r.rule_id} r={r} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── 加载态 Skeleton ────────────────────────────────────────────────────────────

export function ValidationPanelSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-16 bg-gray-100 rounded-xl" />
      <div className="h-12 bg-red-50 rounded-lg" />
      <div className="h-12 bg-amber-50 rounded-lg" />
    </div>
  );
}
