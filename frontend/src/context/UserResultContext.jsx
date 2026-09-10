import { createContext, useContext, useMemo, useState } from "react";

const STORAGE_KEY = "docextract:user-result";

const UserResultContext = createContext(null);

function readPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function persist(value) {
  try {
    if (value) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // localStorage can be unavailable (private browsing etc.) — non-fatal.
  }
}

// Persists the user's corrected result for the *current* extraction. Stored
// payload is scoped to the extraction result_id so edits never bleed into a
// different document's session.
export function UserResultProvider({ children }) {
  const [userResult, setUserResultState] = useState(() => readPersisted());

  const saveUserResult = (resultId, userResultPayload) => {
    const payload = { result_id: resultId, ...userResultPayload, savedAt: new Date().toISOString() };
    setUserResultState(payload);
    persist(payload);
  };

  const resetUserResult = () => {
    setUserResultState(null);
    persist(null);
  };

  const value = useMemo(
    () => ({
      userResult,
      // Returns the saved user_result only when it belongs to this result_id.
      userResultFor: (resultId) =>
        userResult && userResult.result_id === resultId ? userResult : null,
      saveUserResult,
      resetUserResult,
    }),
    [userResult]
  );

  return (
    <UserResultContext.Provider value={value}>
      {children}
    </UserResultContext.Provider>
  );
}

export function useUserResult() {
  const ctx = useContext(UserResultContext);
  if (!ctx) {
    throw new Error("useUserResult must be used within a UserResultProvider");
  }
  return ctx;
}