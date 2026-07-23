import { createContext, useContext, useMemo, useState } from "react";

const STORAGE_KEY = "docextract:last-session";

const ExtractionContext = createContext(null);

function readPersisted() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function persist(value) {
  try {
    if (value) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // sessionStorage can be unavailable (private browsing etc.) - non-fatal
  }
}

export function ExtractionProvider({ children }) {
  const [session, setSessionState] = useState(() => readPersisted());

  const setSession = (value) => {
    setSessionState(value);
    persist(value);
  };

  const clearSession = () => setSession(null);

  const value = useMemo(
    () => ({ session, setSession, clearSession }),
    [session]
  );

  return (
    <ExtractionContext.Provider value={value}>
      {children}
    </ExtractionContext.Provider>
  );
}

export function useExtraction() {
  const ctx = useContext(ExtractionContext);
  if (!ctx) {
    throw new Error("useExtraction must be used within an ExtractionProvider");
  }
  return ctx;
}
