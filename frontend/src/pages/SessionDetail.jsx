import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowLeft, Trophy } from 'lucide-react';
import { interviews } from '../lib/api';

const STATUS_TR = {
  CREATED: 'Oluşturuldu',
  IN_PROGRESS: 'Devam ediyor',
  COMPLETED: 'Tamamlandı',
  ABORTED: 'İptal edildi',
};

export default function SessionDetail() {
  const { id } = useParams();
  const { data, isLoading } = useQuery({
    queryKey: ['session', id], queryFn: () => interviews.get(id),
  });

  if (isLoading) return <div className="card animate-pulse h-40" />;
  if (!data) return null;

  return (
    <div className="space-y-5 max-w-3xl">
      <Link to="/history" className="inline-flex items-center gap-2 text-sm text-white/60 hover:text-white">
        <ArrowLeft size={14} /> Geçmişe dön
      </Link>

      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="card">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-white/50">Oturum</div>
            <h1 className="text-2xl font-semibold">{data.role} · {data.level}</h1>
            <div className="text-sm text-white/50 mt-1">
              {new Date(data.createdAt).toLocaleString('tr-TR')} · {STATUS_TR[data.status] || data.status}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-white/50 mb-1">Genel puan</div>
            <div className="text-3xl font-semibold flex items-center gap-2">
              <Trophy size={20} className="text-brand-400" />
              {data.overallScore != null ? data.overallScore.toFixed(2) : '—'}
            </div>
          </div>
        </div>
      </motion.div>

      <div className="space-y-3">
        {data.questions.map((q, i) => (
          <motion.div
            key={q.id}
            initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="card"
          >
            <div className="text-xs uppercase tracking-wider text-white/50 mb-1">
              Soru {q.ordinal}
            </div>
            <div className="font-medium">{q.prompt}</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
