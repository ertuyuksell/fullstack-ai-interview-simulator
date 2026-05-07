import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { auth } from '../lib/api';
import { useAuth } from '../store/auth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const setSession = useAuth((s) => s.setSession);
  const nav = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const data = await auth.login(email, password);
      setSession(data);
      nav('/');
    } catch (e) {
      setErr(e?.response?.data?.error || 'Giriş başarısız');
    } finally { setBusy(false); }
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="card w-full max-w-md"
      >
        <div className="flex items-center gap-2 mb-6">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 grid place-items-center">
            <Sparkles size={18} />
          </div>
          <div className="font-semibold">Mülakat AI</div>
        </div>
        <h1 className="text-2xl font-semibold mb-1">Tekrar hoş geldin</h1>
        <p className="text-sm text-white/60 mb-6">Pratiğe devam etmek için giriş yap.</p>

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="label">E-posta</label>
            <input className="input" type="email" value={email}
                   onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="label">Şifre</label>
            <input className="input" type="password" value={password}
                   onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {err && <div className="text-sm text-red-400">{err}</div>}
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? 'Giriş yapılıyor…' : 'Giriş yap'}
          </button>
        </form>
        <div className="text-sm text-white/60 mt-6">
          Hesabın yok mu?{' '}
          <Link to="/register" className="text-brand-400 hover:text-brand-300">
            Hesap oluştur
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
