// ── Admin API — 直接调后端 FastAPI，不再依赖 Supabase ──────────────────────

// 通过 Next.js API route 代理，避免浏览器跨域和手机无法访问 localhost 的问题
const API_BASE = "/api/admin/submissions";

// ── Types ────────────────────────────────────────────────────────────────────

export interface QuizSubmission {
  id: string;
  name: string | null;
  destination: string;
  duration_days: number;
  people_count: number | null;
  party_type: string;
  japan_experience: string | null;
  play_mode: string | null;
  budget_focus: string | null;
  styles: string[];
  wechat_id: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// Keep backward compat alias
export type OrderItem = QuizSubmission & {
  order_id: string;
  trip_request_id: string | null;
  sku_id: string;
  amount_cny: number;
  payment_channel: string | null;
  paid_at: string | null;
};

// Convert QuizSubmission to OrderItem shape for existing UI
function toOrderItem(q: QuizSubmission): OrderItem {
  return {
    ...q,
    order_id: q.id,
    trip_request_id: q.id,
    sku_id: "basic_free",
    amount_cny: 0,
    payment_channel: null,
    paid_at: null,
  };
}

// ── Fetch all submissions ────────────────────────────────────────────────────

export async function fetchOrders(status?: string): Promise<OrderItem[]> {
  try {
    let url = API_BASE;
    if (status) {
      url += `?status=${encodeURIComponent(status)}`;
    }

    const res = await fetch(url);
    if (!res.ok) {
      console.error("Failed to fetch submissions:", res.status);
      return [];
    }

    const data: QuizSubmission[] = await res.json();
    return data.map(toOrderItem);
  } catch (e) {
    console.error("Failed to fetch submissions:", e);
    return [];
  }
}

// ── Fetch single submission ──────────────────────────────────────────────────

export async function fetchOrderById(id: string): Promise<OrderItem | null> {
  try {
    const res = await fetch(`${API_BASE}?id=${id}`);
    if (!res.ok) return null;

    const data: QuizSubmission = await res.json();
    return toOrderItem(data);
  } catch {
    return null;
  }
}

// ── Update status ────────────────────────────────────────────────────────────

export async function updateOrderStatus(
  id: string,
  newStatus: string,
  reason?: string
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}?id=${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus, notes: reason || null }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ── Convenience functions ────────────────────────────────────────────────────

export async function fetchPendingReviews(): Promise<OrderItem[]> {
  return fetchOrders("new");
}

export async function publishOrder(id: string): Promise<boolean> {
  return updateOrderStatus(id, "delivered", "admin_publish");
}

export async function rejectOrder(id: string): Promise<boolean> {
  return updateOrderStatus(id, "generating", "admin_reject");
}

export async function confirmPayment(id: string): Promise<boolean> {
  return updateOrderStatus(id, "paid", "admin_confirm_payment");
}

export async function refundOrder(id: string, reason?: string): Promise<boolean> {
  return updateOrderStatus(id, "refunded", reason || "admin_refund");
}

export async function markAsUsing(id: string): Promise<boolean> {
  return updateOrderStatus(id, "using", "admin_mark_using");
}

export async function archiveOrder(id: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}?id=${id}&action=archive`, {
      method: "POST",
    });
    return res.ok;
  } catch {
    return false;
  }
}
