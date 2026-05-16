"use client";

import { OPERATOR_MODES, type OperatorMode } from "../_lib/operators";
import { useOperatorMode } from "./OperatorModeProvider";

export function OperatorModeSwitcher() {
  const { mode, setMode, ready } = useOperatorMode();

  return (
    <div
      role="radiogroup"
      aria-label="Operator mode"
      className="flex items-stretch border border-[color:var(--ss-border-strong)]"
      style={{ backgroundColor: "var(--ss-panel-elevated)" }}
    >
      {OPERATOR_MODES.map((descriptor, index) => {
        const selected = mode === descriptor.value;
        return (
          <button
            key={descriptor.value}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={`${descriptor.label} — ${descriptor.hint}`}
            disabled={!ready}
            onClick={() => setMode(descriptor.value)}
            className="px-3 py-2 font-mono text-[0.62rem] font-black uppercase tracking-widest transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:cursor-not-allowed disabled:opacity-60"
            data-mode={descriptor.value}
            data-selected={selected ? "true" : "false"}
            style={{
              minHeight: "var(--ss-tap-target)",
              minWidth: "var(--ss-tap-target)",
              borderLeft: index === 0 ? "none" : "1px solid var(--ss-border-strong)",
              backgroundColor: selected ? swatchFor(descriptor.value, "panel") : "transparent",
              color: selected ? swatchFor(descriptor.value, "text") : "var(--ss-text-secondary)"
            }}
          >
            {descriptor.label}
          </button>
        );
      })}
    </div>
  );
}

function swatchFor(value: OperatorMode, slot: "panel" | "text"): string {
  if (value === "redline") {
    return slot === "panel" ? "var(--ss-warning-dim)" : "var(--ss-warning)";
  }
  if (value === "mint-signal") {
    return slot === "panel" ? "var(--ss-accent-faint)" : "var(--ss-accent)";
  }
  return slot === "panel" ? "var(--ss-bg)" : "var(--ss-text-primary)";
}
