/**
 * utm.ts — UTM 参数读取与归因上报工具
 *
 * 使用方式：
 * 1. 在表单提交成功拿到 trip_request_id 后，调用 reportAttribution(tripRequestId)
 * 2. utm 参数自动从 localStorage（持久化） + 当前 URL 读取
 */

export interface UtmParams {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  from_tool?: string;
  referral_code?: string;
  landing_page?: string;
  referrer?: string;
}

const STORAGE_KEY = "travel_ai_utm";
const STORAGE_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7天

interface StoredUtm {
  params: UtmParams;
  savedAt: number;
}

/** 从 URL 搜索参数提取 UTM 字段 */
function extractFromUrl(search: string): UtmParams {
  const params = new URLSearchParams(search);
  const result: UtmParams = {};

  const utm_source = params.get("utm_source");
  const utm_medium = params.get("utm_medium");
  const utm_campaign = params.get("utm_campaign");
  const utm_content = params.get("utm_content");
  const from = params.get("from");
  const ref = params.get("ref");

  if (utm_source) result.utm_source = utm_source;
  if (utm_medium) result.utm_medium = utm_medium;
  if (utm_campaign) result.utm_campaign = utm_campaign;
  if (utm_content) result.utm_content = utm_content;
  if (from) result.from_tool = from;
  if (ref) result.referral_code = ref;

  return result;
}

/** 把 UTM 参数持久化到 localStorage（7天TTL） */
export function saveUtmToStorage(params: UtmParams): void {
  if (typeof window === "undefined") return;
  if (Object.keys(params).length === 0) return;
  try {
    const stored: StoredUtm = { params, savedAt: Date.now() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  } catch {
    // localStorage 不可用，忽略
  }
}

/** 从 localStorage 读取已保存的 UTM 参数（过期则丢弃） */
function loadUtmFromStorage(): UtmParams {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const stored: StoredUtm = JSON.parse(raw);
    if (Date.now() - stored.savedAt > STORAGE_TTL_MS) {
      localStorage.removeItem(STORAGE_KEY);
      return {};
    }
    return stored.params;
  } catch {
    return {};
  }
}

/**
 * 获取最终的 UTM 参数（当前 URL 参数优先，fallback 到 localStorage）
 * 同时自动保存当前 URL 的参数到 localStorage
 */
export function collectUtmParams(): UtmParams {
  if (typeof window === "undefined") return {};

  const fromUrl = extractFromUrl(window.location.search);
  const fromStorage = loadUtmFromStorage();

  // 合并：URL 参数优先
  const merged: UtmParams = { ...fromStorage, ...fromUrl };

  // 补充 landing_page 和 referrer
  if (!merged.landing_page) {
    merged.landing_page = window.location.href;
  }
  if (!merged.referrer && document.referrer) {
    merged.referrer = document.referrer;
  }

  // 有新的 URL 参数时保存
  if (Object.keys(fromUrl).length > 0) {
    saveUtmToStorage({ ...fromStorage, ...fromUrl });
  }

  return merged;
}

/**
 * 上报归因数据到后端
 * 在用户提交表单成功、拿到 trip_request_id 后调用。
 * 失败静默处理，不影响主流程。
 */
export async function reportAttribution(
  tripRequestId: string,
  extraParams?: Partial<UtmParams>,
): Promise<void> {
  try {
    const params = { ...collectUtmParams(), ...extraParams };
    if (Object.keys(params).length === 0) return;

    await fetch(`/api/attribution/${tripRequestId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
      keepalive: true, // 允许页面跳转后继续发送
    });
  } catch {
    // 静默处理，不影响主业务流程
  }
}

/**
 * 初始化 UTM 采集（在页面加载时调用，保存当前 URL 的 UTM 参数）
 * 建议在 layout.tsx 的 Client 组件中调用
 */
export function initUtmTracking(): void {
  if (typeof window === "undefined") return;
  const fromUrl = extractFromUrl(window.location.search);
  if (Object.keys(fromUrl).length > 0) {
    saveUtmToStorage({ ...loadUtmFromStorage(), ...fromUrl });
  }
}
