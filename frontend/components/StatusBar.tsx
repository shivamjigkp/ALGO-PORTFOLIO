"use client";

import { useEffect, useState } from "react";

interface StatusBarProps {
  connected: boolean;
  symbolsCount: number;
  activeStructuresCount: number;
  lastUpdated: number | null; // unix seconds
}

export default function StatusBar({
  connected,
  symbolsCount,
  activeStructuresCount,
  lastUpdated,
}: StatusBarProps) {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const secondsAgo =
    lastUpdated && now ? Math.max(0, Math.round(now.getTime() / 1000 - lastUpdated)) : null;

  return (
    <div className="statusbar">
      <div className="left">
        <span className={`conn ${connected ? "" : "off"}`}>
          <span className="dot" />
          {connected ? "Feed connected" : "Feed disconnected"}
        </span>
        {secondsAgo !== null && <span>Last update {secondsAgo}s ago</span>}
        <span>{symbolsCount} symbols tracked</span>
        <span>{activeStructuresCount} active structures</span>
      </div>
      <div>
        TwelveData · 15m · {now ? now.toISOString().slice(11, 19) : "--:--:--"} UTC
      </div>
    </div>
  );
}
