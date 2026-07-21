"use client";

interface TickerBarProps {
  symbols: string[];
  activeSymbol: string;
  onSelect: (symbol: string) => void;
}

export default function TickerBar({ symbols, activeSymbol, onSelect }: TickerBarProps) {
  return (
    <div className="ticker">
      <div className="ticker-brand">
        <span className="dot" />
        MASTERMIND ALGO TRADER
        <span style={{ color: "var(--text-muted)", fontWeight: 400, marginLeft: 6 }}>
          / QuantX
        </span>
      </div>

      {symbols.map((s) => (
        <div
          key={s}
          className="tick"
          onClick={() => onSelect(s)}
          style={{
            cursor: "pointer",
            opacity: s === activeSymbol ? 1 : 0.6,
          }}
        >
          <span className="sym">{s}</span>
        </div>
      ))}
    </div>
  );
}
