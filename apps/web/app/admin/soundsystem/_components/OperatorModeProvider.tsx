"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import {
  DEFAULT_OPERATOR_MODE,
  OPERATOR_MODE_STORAGE_KEY,
  isOperatorMode,
  type OperatorMode
} from "../_lib/operators";

type OperatorModeContextValue = Readonly<{
  mode: OperatorMode;
  setMode: (mode: OperatorMode) => void;
  ready: boolean;
}>;

const OperatorModeContext = createContext<OperatorModeContextValue | null>(null);

export function OperatorModeProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [mode, setModeState] = useState<OperatorMode>(DEFAULT_OPERATOR_MODE);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(OPERATOR_MODE_STORAGE_KEY);
      if (isOperatorMode(stored)) {
        setModeState(stored);
      }
    } catch {
      // localStorage may be unavailable (private mode, storage quota). Fall through to default.
    }
    setReady(true);
  }, []);

  const setMode = useCallback((next: OperatorMode) => {
    setModeState(next);
    try {
      window.localStorage.setItem(OPERATOR_MODE_STORAGE_KEY, next);
    } catch {
      // Swallow — persistence is best-effort, runtime state is the source of truth.
    }
  }, []);

  const value = useMemo<OperatorModeContextValue>(() => ({ mode, setMode, ready }), [mode, setMode, ready]);

  return (
    <OperatorModeContext.Provider value={value}>
      <div
        data-operator-mode={mode}
        data-operator-mode-ready={ready ? "true" : "false"}
        style={{ display: "contents" }}
      >
        {children}
      </div>
    </OperatorModeContext.Provider>
  );
}

export function useOperatorMode(): OperatorModeContextValue {
  const ctx = useContext(OperatorModeContext);
  if (ctx === null) {
    throw new Error("useOperatorMode must be used within OperatorModeProvider");
  }
  return ctx;
}
