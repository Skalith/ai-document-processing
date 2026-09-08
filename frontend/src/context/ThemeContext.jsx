import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { DEFAULT_THEME_ID } from "../theme";

const STORAGE_KEY = "docextract:theme";

const ThemePreferenceContext = createContext(null);

function readInitialTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored || DEFAULT_THEME_ID;
  } catch {
    return DEFAULT_THEME_ID;
  }
}

export function ThemePreferenceProvider({ children }) {
  const [themeId, setThemeIdState] = useState(readInitialTheme);

  const setThemeId = useCallback((nextId) => {
    setThemeIdState(nextId);
    try {
      localStorage.setItem(STORAGE_KEY, nextId);
    } catch {
      // localStorage can be unavailable (private browsing etc.) - non-fatal
    }
  }, []);

  const value = useMemo(() => ({ themeId, setThemeId }), [themeId, setThemeId]);

  return (
    <ThemePreferenceContext.Provider value={value}>
      {children}
    </ThemePreferenceContext.Provider>
  );
}

export function useThemePreference() {
  const ctx = useContext(ThemePreferenceContext);
  if (!ctx) {
    throw new Error("useThemePreference must be used within a ThemePreferenceProvider");
  }
  return ctx;
}