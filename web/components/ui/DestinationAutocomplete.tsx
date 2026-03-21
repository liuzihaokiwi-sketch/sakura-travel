"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ── 类型 ──────────────────────────────────────────────────────────────────────

export interface DestinationOption {
  place_id: string;
  name_zh: string;
  name_en: string;
  region?: string;
  type?: string;
  match_score: number;
}

interface Props {
  value?: string;            // place_id
  displayValue?: string;     // 显示文字（name_zh）
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  /** 选中后回调，带完整选项对象 */
  onSelect: (option: DestinationOption) => void;
  /** 清空回调 */
  onClear?: () => void;
}

// ── API ───────────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

async function fetchSuggestions(q: string): Promise<DestinationOption[]> {
  if (!q.trim()) return [];
  const res = await fetch(
    `${API_BASE}/destinations/autocomplete?q=${encodeURIComponent(q)}&limit=8`,
  );
  if (!res.ok) return [];
  const data = await res.json();
  return (data.results ?? []) as DestinationOption[];
}

// ── 组件 ──────────────────────────────────────────────────────────────────────

export default function DestinationAutocomplete({
  value,
  displayValue,
  placeholder = "输入目的地，如：东京、大阪",
  disabled = false,
  className = "",
  onSelect,
  onClear,
}: Props) {
  const [inputVal, setInputVal] = useState(displayValue ?? "");
  const [suggestions, setSuggestions] = useState<DestinationOption[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 同步外部 displayValue
  useEffect(() => {
    if (displayValue !== undefined) setInputVal(displayValue);
  }, [displayValue]);

  // 点击外部关闭
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const search = useCallback(async (q: string) => {
    if (q.length < 1) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }
    setLoading(true);
    try {
      const results = await fetchSuggestions(q);
      setSuggestions(results);
      setIsOpen(results.length > 0);
      setActiveIdx(-1);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value;
    setInputVal(q);
    if (value && q !== displayValue) onClear?.();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(q), 250);
  };

  const handleSelect = (opt: DestinationOption) => {
    setInputVal(opt.name_zh);
    setSuggestions([]);
    setIsOpen(false);
    onSelect(opt);
  };

  const handleClear = () => {
    setInputVal("");
    setSuggestions([]);
    setIsOpen(false);
    onClear?.();
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (activeIdx >= 0 && suggestions[activeIdx]) handleSelect(suggestions[activeIdx]);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const hasValue = inputVal.trim().length > 0;

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      {/* 输入框 */}
      <div className="relative flex items-center">
        <span className="absolute left-3 text-gray-400 pointer-events-none">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
        </span>

        <input
          ref={inputRef}
          type="text"
          value={inputVal}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => { if (suggestions.length > 0) setIsOpen(true); }}
          placeholder={placeholder}
          disabled={disabled}
          aria-label="目的地搜索"
          aria-autocomplete="list"
          aria-expanded={isOpen}
          className={[
            "w-full pl-9 pr-10 py-2.5 text-sm rounded-lg border outline-none transition-all",
            "placeholder:text-gray-400",
            disabled
              ? "bg-gray-50 text-gray-400 cursor-not-allowed border-gray-200"
              : "bg-white text-gray-900 border-gray-300 hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100",
          ].join(" ")}
        />

        <span className="absolute right-3">
          {loading ? (
            <svg className="w-4 h-4 animate-spin text-indigo-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : hasValue ? (
            <button type="button" onClick={handleClear} aria-label="清除">
              <svg className="w-4 h-4 text-gray-400 hover:text-gray-600" fill="none"
                viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          ) : null}
        </span>
      </div>

      {/* 下拉列表 */}
      {isOpen && suggestions.length > 0 && (
        <ul
          role="listbox"
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden max-h-64 overflow-y-auto"
        >
          {suggestions.map((opt, idx) => (
            <li
              key={opt.place_id}
              role="option"
              aria-selected={idx === activeIdx}
              onMouseDown={(e) => { e.preventDefault(); handleSelect(opt); }}
              onMouseEnter={() => setActiveIdx(idx)}
              className={[
                "flex items-center gap-3 px-4 py-2.5 cursor-pointer text-sm transition-colors",
                idx === activeIdx ? "bg-indigo-50" : "hover:bg-gray-50",
              ].join(" ")}
            >
              <span className="text-base flex-shrink-0">
                {opt.type === "region" ? "🗾" : "🏙️"}
              </span>
              <span className="flex-1 min-w-0">
                <span className="font-medium text-gray-900">{opt.name_zh}</span>
                <span className="text-gray-400 ml-1.5 text-xs">{opt.name_en}</span>
              </span>
              {opt.region && (
                <span className="flex-shrink-0 text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                  {opt.region}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
