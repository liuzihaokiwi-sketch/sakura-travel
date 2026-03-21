"use client";

/**
 * M7: 正式修改计数器组件
 *
 * 自助微调（SwapDrawer）= 无限次，免费，用户自己操作
 * 正式修改 = 有限次（默认 1 次），需要联系客服，有人工介入
 *
 * 本组件显示：
 *   - 剩余正式修改次数
 *   - 发起正式修改的按钮（到达上限时禁用 + 提示）
 *   - 修改记录历史（可折叠）
 */

import { useState } from "react";

// ── 类型 ──────────────────────────────────────────────────────────────────────

interface RevisionRecord {
  id: string;
  created_at: string;
  description: string;
  status: "pending" | "in_progress" | "done";
}

interface Props {
  planId: string;
  maxRevisions?: number;              // 默认 1
  usedRevisions?: number;             // 已使用次数
  revisionRecords?: RevisionRecord[]; // 历史记录
  wechatId?: string;                  // 客服微信号
  onRevisionRequest?: () => void;     // 发起修改回调
}

// ── 工具 ──────────────────────────────────────────────────────────────────────

function statusBadge(s: RevisionRecord["status"]) {
  const map = {
    pending:     { label: "待处理", cls: "bg-amber-100 text-amber-700" },
    in_progress: { label: "处理中", cls: "bg-blue-100 text-blue-700" },
    done:        { label: "已完成", cls: "bg-green-100 text-green-700" },
  };
  return map[s] ?? { label: s, cls: "bg-gray-100 text-gray-500" };
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString("zh-CN", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

// ── 主组件 ────────────────────────────────────────────────────────────────────

export default function RevisionCounter({
  planId,
  maxRevisions = 1,
  usedRevisions = 0,
  revisionRecords = [],
  wechatId = "travelai_service",
  onRevisionRequest,
}: Props) {
  const [showHistory, setShowHistory] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const remaining = Math.max(0, maxRevisions - usedRevisions);
  const canRevise = remaining > 0;

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      // 通知后端发起正式修改
      await fetch(`/api/trips/${planId}/revisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "formal_revision" }),
      });
      setDone(true);
      onRevisionRequest?.();
      setTimeout(() => {
        setShowConfirm(false);
        setDone(false);
      }, 3000);
    } catch {
      // 失败时不阻塞，用户可重试
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">正式修改</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              需要修改行程框架、目的地或天数？联系客服发起正式修改
            </p>
          </div>
          {/* 次数指示器 */}
          <div className="flex items-center gap-1.5">
            {Array.from({ length: maxRevisions }).map((_, i) => (
              <div
                key={i}
                className={`w-3 h-3 rounded-full border-2 transition-colors ${
                  i < usedRevisions
                    ? "bg-gray-300 border-gray-300"
                    : "bg-indigo-500 border-indigo-500"
                }`}
              />
            ))}
            <span className="text-xs text-gray-500 ml-1">
              {remaining}/{maxRevisions} 次
            </span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-5 py-4 space-y-3">
        {/* 区分说明 */}
        <div className="bg-gray-50 rounded-xl p-3 text-xs text-gray-500 space-y-1">
          <div className="flex gap-2">
            <span>🔄</span>
            <span><strong className="text-gray-700">自助微调</strong>：景点/餐厅换一换，无限次，实时生效</span>
          </div>
          <div className="flex gap-2">
            <span>✏️</span>
            <span><strong className="text-gray-700">正式修改</strong>：天数/城市/整体框架调整，共 {maxRevisions} 次机会</span>
          </div>
        </div>

        {/* 发起按钮 */}
        {!showConfirm ? (
          <button
            onClick={() => canRevise && setShowConfirm(true)}
            disabled={!canRevise}
            className={`w-full py-2.5 rounded-xl text-sm font-medium transition-all ${
              canRevise
                ? "bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95"
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
            }`}
          >
            {canRevise
              ? `✏️ 发起正式修改（剩余 ${remaining} 次）`
              : "正式修改次数已用完"}
          </button>
        ) : (
          /* 确认框 */
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 space-y-3">
            {done ? (
              <div className="text-center">
                <p className="text-green-600 font-semibold text-sm">✅ 已发起修改请求</p>
                <p className="text-xs text-gray-500 mt-1">客服会在 24 小时内与您联系</p>
              </div>
            ) : (
              <>
                <p className="text-sm text-gray-700">
                  发起正式修改后，客服会通过微信联系您确认修改内容，并重新生成攻略。
                </p>
                <p className="text-xs text-gray-500">
                  客服微信：<strong className="text-gray-700">{wechatId}</strong>
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowConfirm(false)}
                    className="flex-1 py-2 rounded-lg text-sm border border-gray-200 text-gray-600 hover:bg-gray-50"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleConfirm}
                    disabled={submitting}
                    className="flex-1 py-2 rounded-lg text-sm bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-60"
                  >
                    {submitting ? "提交中…" : "确认发起"}
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* 历史记录 */}
        {revisionRecords.length > 0 && (
          <div>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              {showHistory ? "▲ 收起历史" : `▶ 修改记录（${revisionRecords.length}）`}
            </button>
            {showHistory && (
              <div className="mt-2 space-y-2">
                {revisionRecords.map((r) => {
                  const badge = statusBadge(r.status);
                  return (
                    <div key={r.id}
                      className="flex items-start gap-2 text-xs bg-gray-50 rounded-lg px-3 py-2">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${badge.cls} flex-shrink-0`}>
                        {badge.label}
                      </span>
                      <div className="min-w-0">
                        <p className="text-gray-700 truncate">{r.description}</p>
                        <p className="text-gray-400">{fmtDate(r.created_at)}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
