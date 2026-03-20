const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface OrderItem {
  order_id: string;
  trip_request_id: string | null;
  sku_id: string;
  status: string;
  amount_cny: number;
  payment_channel: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
  wechat_id: string | null;
  destination: string | null;
  duration_days: number | null;
}

export async function fetchOrders(status?: string): Promise<OrderItem[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limit", "200");

  const res = await fetch(`${API_BASE}/orders?${params}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    // Fallback: return empty for demo / when backend is down
    console.error("Failed to fetch orders:", res.status);
    return [];
  }

  const data = await res.json();
  return data.orders || [];
}

export async function fetchOrderById(id: string): Promise<OrderItem | null> {
  const res = await fetch(`${API_BASE}/orders/${id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function updateOrderStatus(
  id: string,
  newStatus: string,
  reason?: string
): Promise<boolean> {
  const res = await fetch(`${API_BASE}/orders/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_status: newStatus, reason }),
  });
  return res.ok;
}

export async function fetchPendingReviews(): Promise<OrderItem[]> {
  return fetchOrders("review");
}

export async function publishOrder(id: string): Promise<boolean> {
  return updateOrderStatus(id, "delivered", "admin_publish");
}

export async function rejectOrder(id: string): Promise<boolean> {
  return updateOrderStatus(id, "generating", "admin_reject");
}
