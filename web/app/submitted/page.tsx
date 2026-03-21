import { redirect } from "next/navigation";

// /submitted 已废弃，新流程为 /quiz → /sample/[id]
// 保留此文件防止旧链接 404，直接 redirect 到 /quiz
export default function SubmittedPage() {
  redirect("/quiz");
}