import { useEffect, useMemo, useState } from "react";

export function TimerPanel({
  preset,
  endsAt,
  pausedRemainingMs,
  onToggle,
  onPauseToggle,
}: {
  preset: 30 | 60 | 90;
  endsAt: number | null;
  pausedRemainingMs: number | null;
  onToggle: (preset: 30 | 60 | 90) => void;
  onPauseToggle: () => void;
}) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 200);
    return () => window.clearInterval(timer);
  }, []);

  const remainingMs = useMemo(() => {
    if (pausedRemainingMs !== null) return pausedRemainingMs;
    if (!endsAt) return preset * 1000;
    return Math.max(0, endsAt - now);
  }, [endsAt, now, pausedRemainingMs, preset]);

  const remainingSeconds = remainingMs / 1000;
  const isWarning = remainingSeconds <= 10 && preset !== 90;
  const isFlash = remainingMs === 0 && endsAt !== null;
  const presets: Array<30 | 60 | 90> = [30, 60, 90];

  return (
    <section className={`timer-panel ${isWarning ? "warning" : ""} ${isFlash ? "flash" : ""}`}>
      <div className="timer-presets">
        {presets.map((item) => (
          <button key={item} className={`timer-chip ${preset === item ? "active" : ""}`} onClick={() => onToggle(item)}>
            {item === 90 ? "1.5 min" : item === 60 ? "1 min" : "30 sec"}
          </button>
        ))}
      </div>
      <div className="timer-readout">
        {Math.floor(remainingSeconds / 60)
          .toString()
          .padStart(2, "0")}
        :
        {Math.floor(remainingSeconds % 60)
          .toString()
          .padStart(2, "0")}
      </div>
      <button className="ghost-button" onClick={onPauseToggle}>
        {pausedRemainingMs !== null ? "Продолжить" : "Пауза"}
      </button>
    </section>
  );
}
