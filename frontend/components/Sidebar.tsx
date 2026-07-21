"use client";

import { useState } from "react";

interface SidebarProps {
  symbols: string[];
  activeSymbol: string;
  activeSymbolPrice: number | null;
  activeStructureCount: number;
  newSymbol: string;
  onNewSymbolChange: (value: string) => void;
  onSelect: (symbol: string) => void;
  onAddSymbol: () => void;
}

export default function Sidebar({
  symbols,
  activeSymbol,
  activeSymbolPrice,
  activeStructureCount,
  newSymbol,
  onNewSymbolChange,
  onSelect,
  onAddSymbol,
}: SidebarProps) {
  const [search, setSearch] = useState("");

  const filtered = symbols.filter((s) =>
    s.toLowerCase().replace("/", "").includes(search.toLowerCase().replace("/", ""))
  );

  return (
    <div className="sidebar">
      <div className="sidebar-label">Watchlist</div>

      <div style={{ padding: "0 18px 12px" }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search symbol…"
          style={{
            width: "100%",
            background: "var(--panel-alt)",
            border: "1px solid var(--hairline)",
            color: "var(--text-primary)",
            borderRadius: 4,
            padding: "6px 8px",
            fontSize: 12,
          }}
        />
      </div>

      {symbols.length === 0 && (
        <div style={{ padding: "0 18px", fontSize: 12, color: "var(--text-muted)" }}>
          No symbols yet — add one below.
        </div>
      )}

      {symbols.length > 0 && filtered.length === 0 && (
        <div style={{ padding: "0 18px", fontSize: 12, color: "var(--text-muted)" }}>
          No match for &quot;{search}&quot;.
        </div>
      )}

      {filtered.map((s) => {
        const isActive = s === activeSymbol;
        return (
          <button
            key={s}
            onClick={() => onSelect(s)}
            className={`sym-row ${isActive ? "active" : ""}`}
          >
            <div className="name">{s}</div>
            <div className="val mono">
              {isActive && activeSymbolPrice !== null ? activeSymbolPrice.toFixed(4) : ""}
              {isActive && activeStructureCount > 0 && (
                <span className="badge-count hot">{activeStructureCount}</span>
              )}
            </div>
          </button>
        );
      })}

      <div style={{ padding: "16px 18px 0" }}>
        <input
          value={newSymbol}
          onChange={(e) => onNewSymbolChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onAddSymbol()}
          placeholder="e.g. XAU/USD"
          style={{
            width: "100%",
            background: "var(--panel-alt)",
            border: "1px solid var(--hairline)",
            color: "var(--text-primary)",
            borderRadius: 4,
            padding: "7px 8px",
            fontSize: 12,
            marginBottom: 8,
          }}
        />
        <button
          onClick={onAddSymbol}
          style={{
            width: "100%",
            background: "transparent",
            border: "1px dashed var(--hairline)",
            color: "var(--text-muted)",
            borderRadius: 4,
            padding: 8,
            fontSize: 12,
          }}
        >
          + Add symbol
        </button>
      </div>
    </div>
  );
}