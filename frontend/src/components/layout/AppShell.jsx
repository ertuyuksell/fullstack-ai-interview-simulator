import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, History, Plus, LogOut, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../../store/auth';
import { useSessionGuard } from '../../hooks/useSessionGuard';

const links = [
  { to: '/', label: 'Panel', icon: LayoutDashboard },
  { to: '/history', label: 'Geçmiş', icon: History },
  { to: '/new', label: 'Yeni Mülakat', icon: Plus },
];

export default function AppShell() {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const nav = useNavigate();
  useSessionGuard();

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 shrink-0 border-r border-white/5 bg-black/30 backdrop-blur-md p-5 flex flex-col">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 grid place-items-center">
            <Sparkles size={18} />
          </div>
          <div>
            <div className="font-semibold tracking-tight">Mülakat AI</div>
            <div className="text-xs text-white/40">v1.0</div>
          </div>
        </div>

        <nav className="space-y-1 flex-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition ${
                  isActive
                    ? 'bg-white/10 text-white shadow-glow'
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon size={16} /> {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/5 pt-4">
          <div className="text-sm font-medium truncate">{user?.fullName || 'Kullanıcı'}</div>
          <div className="text-xs text-white/40 truncate mb-3">{user?.email}</div>
          <button
            className="btn-ghost w-full"
            onClick={() => {
              logout();
              nav('/login');
            }}
          >
            <LogOut size={14} /> Çıkış yap
          </button>
        </div>
      </aside>

      <motion.main
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="flex-1 min-w-0 p-8 overflow-y-auto"
      >
        <Outlet />
      </motion.main>
    </div>
  );
}
