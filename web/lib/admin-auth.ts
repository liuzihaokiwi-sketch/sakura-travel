import { NextRequest } from "next/server"

type AdminAuthResult = {
  ok: boolean
}

function readBearerToken(request: NextRequest): string | null {
  const auth = request.headers.get("authorization") || ""
  if (!auth.startsWith("Bearer ")) {
    return null
  }
  return auth.slice("Bearer ".length).trim() || null
}

export async function requireAdminSession(request: NextRequest): Promise<AdminAuthResult> {
  const configuredToken = process.env.ADMIN_API_TOKEN?.trim()
  if (!configuredToken) {
    // Keep admin routes usable in local/dev when no shared secret is configured.
    return { ok: process.env.NODE_ENV !== "production" }
  }

  const headerToken =
    request.headers.get("x-admin-token") ||
    readBearerToken(request) ||
    request.cookies.get("admin_token")?.value ||
    ""

  return { ok: headerToken.trim() === configuredToken }
}
