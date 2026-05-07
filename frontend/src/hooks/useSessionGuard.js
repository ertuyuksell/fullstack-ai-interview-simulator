import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/auth';

const IDLE_LIMIT_MS = 30 * 60 * 1000; // 30 dakika hareketsizlik
const CHECK_INTERVAL_MS = 30 * 1000;  // 30 saniyede bir kontrol

const ACTIVITY_EVENTS = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];

export function useSessionGuard() {
  const nav = useNavigate();

  useEffect(() => {
    const { touch } = useAuth.getState();

    let throttle = 0;
    const onActivity = () => {
      const now = Date.now();
      if (now - throttle < 5000) return; // 5 saniyede en fazla bir kez yaz
      throttle = now;
      touch();
    };

    ACTIVITY_EVENTS.forEach((e) => window.addEventListener(e, onActivity, { passive: true }));

    const interval = setInterval(() => {
      const { token, expiresAt, lastActivityAt, logout } = useAuth.getState();
      if (!token) return;

      const now = Date.now();
      const tokenExpired = expiresAt && now >= expiresAt;
      const idleTooLong = lastActivityAt && now - lastActivityAt > IDLE_LIMIT_MS;

      if (tokenExpired || idleTooLong) {
        logout();
        nav('/login', { replace: true });
      }
    }, CHECK_INTERVAL_MS);

    return () => {
      ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, onActivity));
      clearInterval(interval);
    };
  }, [nav]);
}
