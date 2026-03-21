/**
 * 复制文本到剪贴板，兼容 HTTP 环境和移动端。
 * 优先用 Clipboard API，不可用时降级到 execCommand，
 * 再不行弹 prompt 让用户手动复制。
 */
export async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // fallthrough to execCommand
    }
  }

  // execCommand fallback（HTTP 或旧浏览器）
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.cssText = "position:fixed;left:-9999px;top:-9999px;opacity:0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try {
    const ok = document.execCommand("copy");
    if (!ok) throw new Error("execCommand failed");
  } catch {
    window.prompt("请长按复制：", text);
  } finally {
    document.body.removeChild(ta);
  }
}
