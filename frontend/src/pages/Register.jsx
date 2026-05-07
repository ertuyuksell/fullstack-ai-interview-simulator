import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { auth } from '../lib/api';
import { useAuth } from '../store/auth';

export default function Register() {
  const [form, setForm] = useState({ email: '', password: '', fullName: '' });
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const setSession = useAuth((s) => s.setSession);
  const nav = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const data = await auth.register(form);
      setSession(data);
      nav('/');
    } catch (e) {
      setErr(e?.response?.data?.error || 'Kayıt başarısız');
    } finally { setBusy(false); }
  }

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="card w-full max-w-md"
      >
        <h1 className="text-2xl font-semibold mb-1">Hesabını oluştur</h1>
        <p className="text-sm text-white/60 mb-6">Ücretsiz, kredi kartı gerekmez.</p>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="label">Ad Soyad</label>
            <input className="input" value={form.fullName} onChange={update('fullName')} required />
          </div>
          <div>
            <label className="label">E-posta</label>
            <input className="input" type="email" value={form.email} onChange={update('email')} required />
          </div>
          <div>
            <label className="label">Şifre</label>
            <input className="input" type="password" value={form.password}
                   onChange={update('password')} minLength={8} required />
          </div>
          {err && <div className="text-sm text-red-400">{err}</div>}
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? 'Oluşturuluyor…' : 'Hesap oluştur'}
          </button>
        </form>
        <div className="text-sm text-white/60 mt-6">
          Zaten hesabın var mı?{' '}
          <Link to="/login" className="text-brand-400 hover:text-brand-300">Giriş yap</Link>
        </div>
      </motion.div>
    </div>
  );
}
