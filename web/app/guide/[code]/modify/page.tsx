"use client";

import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

type Role = "ai" | "user";

interface Message {
  role: Role;
  content: string;
  quickReplies?: string[];
  awaitingConfirm?: boolean;
}

const WELCOME_MESSAGE: Message = {
  role: "ai",
  content:
    "你好！看完前面的方案后，想调整哪里？\n\n比如「第二天想多安排购物」，或者「晚餐想换便宜一点的」。",
};

export default function ModifyPage() {
  const params = useParams();
  const router = useRouter();
  const code = params.code as string;

  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [canConfirm, setCanConfirm] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [modifyDone, setModifyDone] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading || confirmed) return;
    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      await fetch(`/api/guide/${code}/modify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
    } catch {
      // ignore errors, show mock reply
    }

    // 模拟 AI 回复（后续可换为真实 SSE 流式回复）
    const aiReply = mockAIReply(text);
    setMessages((prev) => [...prev, aiReply]);
    if (aiReply.awaitingConfirm) setCanConfirm(true);
    setLoading(false);
  };

  const handleConfirmModify = async () => {
    setProcessing(true);
    setConfirmed(true);
    try {
      await fetch(`/api/guide/${code}/modify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "__confirm__", confirmed: true }),
      });
    } catch {
      // ignore errors
    }
    await new Promise((r) => setTimeout(r, 5000));
    setModifyDone(true);
    setProcessing(false);
  };

  if (modifyDone) {
    router.push(`/guide/${code}`);
    return null;
  }

  return (
    <div
      style={{
        backgroundColor: "#FBF7F0",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* 顶部 */}
      <div
        style={{
          backgroundColor: "#FFFFFF",
          borderBottom: "1px solid #E8E0D6",
          padding: "12px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Link
          href={`/guide/${code}`}
          style={{
            fontSize: "14px",
            color: "#8B7E74",
            textDecoration: "none",
            display: "flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          ← 返回查看
        </Link>
        <span
          style={{
            fontSize: "13px",
            color: "#A69B91",
            backgroundColor: "#F5F0E8",
            padding: "4px 12px",
            borderRadius: "20px",
          }}
        >
          一轮免费修改
        </span>
      </div>

      {/* 对话区 */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "24px",
          maxWidth: "720px",
          margin: "0 auto",
          width: "100%",
        }}
      >
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} onQuickReply={sendMessage} disabled={confirmed} />
        ))}
        {loading && <TypingIndicator />}
        {processing && (
          <div
            style={{
              textAlign: "center",
              padding: "24px",
              color: "#8B7E74",
              fontSize: "14px",
            }}
          >
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>⚙️</div>
            <p>正在根据你的意见调整方案…</p>
            <p style={{ fontSize: "13px", color: "#A69B91", marginTop: "4px" }}>约 5 分钟</p>
          </div>
        )}
        {confirmed && !processing && !modifyDone && (
          <div
            style={{
              textAlign: "center",
              padding: "24px",
              color: "#4A8B6E",
              fontSize: "14px",
            }}
          >
            ✓ 修改已提交，正在更新…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 确认修改提示 */}
      {canConfirm && !confirmed && (
        <div
          style={{
            backgroundColor: "#F5F0E8",
            padding: "16px 24px",
            borderTop: "1px solid #E8E0D6",
          }}
        >
          <div style={{ maxWidth: "720px", margin: "0 auto" }}>
            <p style={{ fontSize: "13px", color: "#8B7E74", marginBottom: "10px" }}>
              满意了吗？确认后将根据你的意见重新调整（约5分钟）
            </p>
            <button
              onClick={handleConfirmModify}
              style={{
                width: "100%",
                padding: "14px",
                borderRadius: "12px",
                border: "none",
                backgroundColor: "#C65D3E",
                color: "#FFFFFF",
                fontSize: "15px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              确认这次修改 →
            </button>
          </div>
        </div>
      )}

      {/* 输入框 */}
      {!confirmed && (
        <div
          style={{
            backgroundColor: "#FFFFFF",
            borderTop: "1px solid #E8E0D6",
            padding: "16px 24px",
          }}
        >
          <div
            style={{
              maxWidth: "720px",
              margin: "0 auto",
              display: "flex",
              gap: "10px",
              alignItems: "flex-end",
            }}
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(input);
                }
              }}
              placeholder="输入你的想法…（Enter 发送，Shift+Enter 换行）"
              rows={2}
              style={{
                flex: 1,
                padding: "12px 14px",
                borderRadius: "10px",
                border: "1.5px solid #E0D8CE",
                backgroundColor: "#FFFFFF",
                fontSize: "14px",
                color: "#3D3029",
                outline: "none",
                resize: "none",
                lineHeight: 1.5,
              }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              style={{
                padding: "12px 20px",
                borderRadius: "10px",
                border: "none",
                backgroundColor: input.trim() && !loading ? "#C65D3E" : "#E0D8CE",
                color: "#FFFFFF",
                fontSize: "14px",
                fontWeight: 600,
                cursor: input.trim() && !loading ? "pointer" : "not-allowed",
                transition: "background-color 200ms ease",
                flexShrink: 0,
              }}
            >
              发送
            </button>
          </div>
        </div>
      )}

      {/* 已完成修改后的只读提示 */}
      {confirmed && !processing && (
        <div
          style={{
            backgroundColor: "#FFFFFF",
            borderTop: "1px solid #E8E0D6",
            padding: "16px 24px",
            textAlign: "center",
            fontSize: "13px",
            color: "#8B7E74",
          }}
        >
          本次修改已完成。如需再次调整请联系客服。
        </div>
      )}
    </div>
  );
}

// ─── 消息气泡 ─────────────────────────────────────────────────────────────────

function MessageBubble({
  message,
  onQuickReply,
  disabled,
}: {
  message: Message;
  onQuickReply: (text: string) => void;
  disabled: boolean;
}) {
  const isAI = message.role === "ai";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isAI ? "flex-start" : "flex-end",
        marginBottom: "16px",
        gap: "10px",
        alignItems: "flex-end",
      }}
    >
      {isAI && (
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            backgroundColor: "#2D4A3E",
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "14px",
            flexShrink: 0,
          }}
        >
          🤖
        </div>
      )}
      <div style={{ maxWidth: "80%", display: "flex", flexDirection: "column", gap: "8px" }}>
        <div
          style={{
            padding: "12px 16px",
            borderRadius: isAI ? "4px 16px 16px 16px" : "16px 4px 16px 16px",
            backgroundColor: isAI ? "#FFFFFF" : "#2D4A3E",
            color: isAI ? "#3D3029" : "#FFFFFF",
            fontSize: "14px",
            lineHeight: 1.7,
            boxShadow: "0 1px 3px rgba(61, 48, 41, 0.08)",
            whiteSpace: "pre-wrap",
          }}
        >
          {message.content}
        </div>
        {isAI && message.quickReplies && !disabled && (
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {message.quickReplies.map((reply) => (
              <button
                key={reply}
                onClick={() => onQuickReply(reply)}
                style={{
                  padding: "7px 14px",
                  borderRadius: "20px",
                  border: "1.5px solid #2D4A3E",
                  backgroundColor: "transparent",
                  color: "#2D4A3E",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 200ms ease",
                }}
              >
                {reply}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "10px",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          width: "32px",
          height: "32px",
          borderRadius: "50%",
          backgroundColor: "#2D4A3E",
          color: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "14px",
          flexShrink: 0,
        }}
      >
        🤖
      </div>
      <div
        style={{
          padding: "12px 16px",
          borderRadius: "4px 16px 16px 16px",
          backgroundColor: "#FFFFFF",
          boxShadow: "0 1px 3px rgba(61, 48, 41, 0.08)",
          display: "flex",
          gap: "4px",
          alignItems: "center",
        }}
      >
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              backgroundColor: "#D6CFC6",
              animation: `bounce 1s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
        <style>{`
          @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
          }
        `}</style>
      </div>
    </div>
  );
}

// 模拟 AI 回复（替换为真实 API）
function mockAIReply(userText: string): Message {
  const lower = userText.toLowerCase();
  if (lower.includes("第二天") || lower.includes("day2") || lower.includes("太紧")) {
    return {
      role: "ai",
      content:
        "明白，你希望：\n· 第二天从3个景点减到2个\n· 保留岚山竹林和小火车\n· 去掉天龙寺，下午留出自由时间\n\n是这样吗？",
      quickReplies: ["是的 ✓", "不对，我再说"],
      awaitingConfirm: true,
    };
  }
  if (lower.includes("是的") || lower.includes("对") || lower.includes("✓")) {
    return {
      role: "ai",
      content:
        "好的，我记下来了。还有其他想调整的地方吗？\n\n如果没有了，可以点击下方「确认这次修改」，我会据此重新生成你的手账。",
      quickReplies: ["没有了，确认修改"],
      awaitingConfirm: true,
    };
  }
  return {
    role: "ai",
    content:
      "收到。让我理解一下你的意思——\n\n" +
      `你希望：${userText}\n\n这样理解对吗？`,
    quickReplies: ["对的", "不太准确"],
    awaitingConfirm: false,
  };
}
