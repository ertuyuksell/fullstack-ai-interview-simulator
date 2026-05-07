import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Calendar, Trophy } from 'lucide-react';
import { interviews } from '../lib/api';

export default function History() {
  const { data = [], isLoading } = useQuery({
    queryKey: ['sessions'], queryFn: interviews.list,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold">Mülakat geçmişi</h1>
      {isLoading ? (
        <div className="card animate-pulse h-40" />
      ) : data.length === 0 ? (
        <div className="card text-white/60">
          Henüz hiç mülakat yapmadın. <Link to="/new" className="text-brand-400">Yeni mülakat başlat →</Link>
        </div>
      ) : (
        <ul className="grid gap-3">
          {data.map((s, i) => (
            <motion.li
              key={s.id}
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <Link to={`/sessions/${s.id}`} className="card flex items-center justify-between hover:border-white/15 transition">
                <div>
                  <div className="font-medium">{s.role} · {s.level}</div>
                  <div className="text-xs text-white/40 flex items-center gap-1.5 mt-1">
                    <Calendar size={12} /> {new Date(s.createdAt).toLocaleString('tr-TR')}
                  </div>
                </div>
                <div className="flex items-center gap-2 text-brand-300">
                  <Trophy size={14} />
                  <span className="font-semibold">
                    {s.overallScore != null ? s.overallScore.toFixed(2) : '—'}
                  </span>
                </div>
              </Link>
            </motion.li>
          ))}
        </ul>
      )}
    </div>
  );
}
