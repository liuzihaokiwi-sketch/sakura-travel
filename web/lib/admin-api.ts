import { supabase } from "@/lib/supabase";

// ── Types ────────────────────────────────────────────────────────────────────

export interface QuizSubmission {
  id: string;
  destination: string;
  duration_days: number;
  party_type: string;
  japan_experience: string | null;
  play_mode: string | null;
  styles: string[];
  wechat_id: string;
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
  let query = supabase
    .from("quiz_submissions")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(200);

  if (status) {
    query = query.eq("status", status);
  }

  const { data, error } = await query;

  if (error) {
    console.error("Failed to fetch submissions:", error);
    return [];
  }

  return (data || []).map(toOrderItem);
}

// ── Fetch single submission ──────────────────────────────────────────────────

export async function fetchOrderById(id: string): Promise<OrderItem | null> {
  const { data, error } = await supabase
    .from("quiz_submissions")
    .select("*")
    .eq("id", id)
    .single();

  if (error || !data) return null;
  return toOrderItem(data);
}

// ── Update status ────────────────────────────────────────────────────────────

export async function updateOrderStatus(
  id: string,
  newStatus: string,
  reason?: string
): Promise<boolean> {
  const { error } = await supabase
    .from("quiz_submissions")
    .update({
      status: newStatus,
      notes: reason || null,
    })
    .eq("id", id);

  return !error;
}

// ── Convenience functions ────────────────────────────────────────────────────

export async function fetchPendingReviews(): Promise<OrderItem[]> {
  return fetchOrders("new");
}

export async function publishOrder(id: string): Promise<boolean> {
  return updateOrderStatus(id, "delivered", "admin_publish");
}

export async function rejectOrder(id: string): Promise<boolean> {
  return updateOrderStatus(id, "rejected", "admin_reject");
}

export async function confirmPayment(id: string): Promise<boolean> {
  return updateOrderStatus(id, "paid", "admin_confirm_payment");
}

export async function refundOrder(id: string, reason?: string): Promise<boolean> {
  return updateOrderStatus(id, "refunded", reason || "admin_refund");
}