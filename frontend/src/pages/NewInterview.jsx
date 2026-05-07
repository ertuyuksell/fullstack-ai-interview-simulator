import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { interviews } from '../lib/api';

const ROLES = [
  { key: 'Backend Engineer', label: 'Backend Geliştirici' },
  { key: 'Frontend Engineer', label: 'Frontend Geliştirici' },
  { key: 'Data Scientist', label: 'Veri Bilimci' },
  { key: 'Product Manager', label: 'Ürün Yöneticisi' },
];

const LEVELS = [
  { key: 'junior', label: 'Junior' },
  { key: 'mid', label: 'Orta' },
  { key: 'senior', label: 'Kıdemli' },
];

export default function NewInterview() {
  const [role, setRole] = useState(ROLES[0].key);
  const [level, setLevel] = useState('mid');
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  async function start() {
    setBusy(true);
    try {
      const s = await interviews.create(role, level);
      nav(`/interviews/${s.id}`);
    } finally { setBusy(false); }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-semibold mb-1">Yeni mülakat başlat</h1>
        <p className="text-white/60 mb-6">Bir rol ve zorluk seç, soruları biz hazırlayalım.</p>
        <div className="card space-y-5">
          <div>
            <label className="label">Rol</label>
            <div className="grid grid-cols-2 gap-2">
              {ROLES.map((r) => (
                <button key={r.key} onClick={() => setRole(r.key)}
                  className={`px-3 py-3 rounded-xl text-sm border transition text-left ${
                    role === r.key ? 'border-brand-500 bg-brand-500/10' : 'border-white/10 hover:border-white/20'
                  }`}>{r.label}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Seviye</label>
            <div className="flex gap-2">
              {LEVELS.map((l) => (
                <button key={l.key} onClick={() => setLevel(l.key)}
                  className={`px-4 py-2 rounded-xl text-sm border transition ${
                    level === l.key ? 'border-accent-500 bg-accent-500/10' : 'border-white/10 hover:border-white/20'
                  }`}>{l.label}</button>
              ))}
            </div>
          </div>
          <button className="btn-primary w-full" onClick={start} disabled={busy}>
            {busy ? 'Hazırlanıyor…' : 'Mülakatı başlat'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
