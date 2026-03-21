"use client";
import React, { createContext, useContext, useState, useCallback } from "react";

export interface FormData {
  // Step 1 — 目的地与日期
  cities: Array<{ place_id: string; name: string; name_zh: string; nights: number }>;
  travel_start_date: string;
  travel_end_date: string;
  duration_days: number;
  date_flexible: boolean;
  // Step 2 — 同行人
  party_type: string;
  party_size: number;
  party_ages: number[];
  has_elderly: boolean;
  has_children: boolean;
  children_ages: number[];
  special_needs: string;
  // Step 3 — 预算住宿
  budget_level: string;
  budget_total_jpy: number | null;
  accommodation_pref: string[];
  hotel_area_pref: string;
  hotel_booking_status: string;
  booked_hotels: Array<{ name: string; area: string; check_in: string; check_out: string }>;
  // Step 4 — 兴趣
  must_have_tags: string[];
  nice_to_have_tags: string[];
  avoid_tags: string[];
  food_preferences: string[];
  food_restrictions: string[];
  food_restrictions_note: string;
  must_go_places: string[];
  dont_want_places: string[];
  // Step 5 — 节奏
  pace_preference: string;
  trip_style: string;
  stamina_level: string;
  wake_up_time: string;
  fixed_events: Array<{ date: string; time: string; name: string; location: string }>;
  free_text_wishes: string;
  // Step 6 — 交通
  transport_locked: boolean;
  arrival_date: string;
  arrival_time: string;
  arrival_place: string;
  departure_date: string;
  departure_time: string;
  departure_place: string;
  has_jr_pass: boolean;
  jr_pass_type: string;
  has_pocket_wifi: boolean;
  transport_notes: string;
}

const EMPTY_FORM: FormData = {
  cities: [], travel_start_date: "", travel_end_date: "", duration_days: 5, date_flexible: false,
  party_type: "couple", party_size: 2, party_ages: [], has_elderly: false, has_children: false,
  children_ages: [], special_needs: "",
  budget_level: "mid", budget_total_jpy: null, accommodation_pref: [], hotel_area_pref: "",
  hotel_booking_status: "not_booked", booked_hotels: [],
  must_have_tags: [], nice_to_have_tags: [], avoid_tags: [], food_preferences: [],
  food_restrictions: [], food_restrictions_note: "", must_go_places: [], dont_want_places: [],
  pace_preference: "balanced", trip_style: "mixed", stamina_level: "medium", wake_up_time: "08:00",
  fixed_events: [], free_text_wishes: "",
  transport_locked: false, arrival_date: "", arrival_time: "", arrival_place: "",
  departure_date: "", departure_time: "", departure_place: "",
  has_jr_pass: false, jr_pass_type: "", has_pocket_wifi: false, transport_notes: "",
};

interface FormCtx {
  data: FormData;
  update: (patch: Partial<FormData>) => void;
  currentStep: number;
  setStep: (n: number) => void;
  saving: boolean;
  setSaving: (v: boolean) => void;
  errors: Record<string, string>;
  setErrors: (e: Record<string, string>) => void;
}

const Ctx = createContext<FormCtx | null>(null);

export function FormProvider({
  children,
  initial,
}: {
  children: React.ReactNode;
  initial?: Partial<FormData>;
}) {
  const [data, setData] = useState<FormData>({ ...EMPTY_FORM, ...initial });
  const [currentStep, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const update = useCallback((patch: Partial<FormData>) => {
    setData((prev) => ({ ...prev, ...patch }));
  }, []);

  return (
    <Ctx.Provider value={{ data, update, currentStep, setStep, saving, setSaving, errors, setErrors }}>
      {children}
    </Ctx.Provider>
  );
}

export function useForm() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useForm must be used within FormProvider");
  return ctx;
}
