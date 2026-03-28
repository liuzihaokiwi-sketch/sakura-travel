import { redirect } from "next/navigation";

// /tools/sakura → 重定向到已有的 /rush 页（保留 ISR 和完整功能）
export default function SakuraToolPage() {
  redirect("/rush");
}
