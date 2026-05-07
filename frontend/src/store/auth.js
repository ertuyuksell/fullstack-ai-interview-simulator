import { create } from 'zustand';
import { persist } from 'zustand/middleware';

function decodeExp(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch { return null; }
}

export const useAuth = create(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      expiresAt: null,
      lastActivityAt: null,
      setSession: ({ token, email, fullName }) =>
        set({
          token,
          user: { email, fullName },
          expiresAt: decodeExp(token),
          lastActivityAt: Date.now(),
        }),
      touch: () => {
        if (get().token) set({ lastActivityAt: Date.now() });
      },
      logout: () => set({ token: null, user: null, expiresAt: null, lastActivityAt: null }),
    }),
    { name: 'ai-interview-auth' }
  )
);
