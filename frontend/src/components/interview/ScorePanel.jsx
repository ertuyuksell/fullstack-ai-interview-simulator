import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Smile, Volume2, Gauge, Activity, Repeat } from 'lucide-react';

const EMOTION_TR = {
  angry: 'kızgın', disgust: 'tiksinti', fear: 'korku',
  happy: 'mutlu', sad: 'üzgün', surprise: 'şaşkın',
  neutral: 'nötr', calm: 'sakin',
  hap: 'mutlu', neu: 'nötr', ang: 'kızgın', fea: 'korku',
};

const trEmotion = (v) => v ? (EMOTION_TR[String(v).toLowerCase()] || String(v).toLowerCase()) : '—';

const Bar = ({ value }) => (
  <div className="h-2 rounded-full bg-white/10 overflow-hidden">
    <motion.div
      initial={{ width: 0 }} animate={{ width: `${Math.round((value ?? 0) * 100)}%` }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="h-full bg-gradient-to-r from-brand-500 to-accent-400"
    />
  </div>
);

export default function ScorePanel({ score }) {
  const f = score?.features || {};

  return (
    <div className="card h-fit sticky top-6">
      <div className="text-xs uppercase tracking-wider text-white/50 mb-1">Anlık geri bildirim</div>
      <h3 className="text-lg font-semibold mb-4">AI analizi</h3>

      <AnimatePresence mode="wait">
        {!score ? (
          <motion.div
            key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="text-sm text-white/50 leading-relaxed"
          >
            Cevabını gönder; özgüven, cevap kalitesi, duygu ve dil özellikleri analiz edilecek.
          </motion.div>
        ) : (
          <motion.div
            key="score" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
            className="space-y-5"
          >
            <Row icon={Gauge} label="Özgüven" value={score.confidenceScore} />
            <Row icon={Brain} label="Cevap kalitesi" value={score.answerQualityScore} />

            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/5">
              <Tag icon={Smile} label="Yüz" value={trEmotion(score.facialEmotion)} />
              <Tag icon={Volume2} label="Ses" value={trEmotion(score.speechEmotion)} />
            </div>

            <div className="pt-2 border-t border-white/5 space-y-2">
              <Mini icon={Activity} label="Tutarlılık"
                    value={f.coherence_score} format="pct" />
              <Mini icon={Repeat} label="Kararsızlık"
                    value={f.hesitation_density} format="pct" inverse />
              <Mini icon={Activity} label="Cümle yapısı"
                    value={f.unique_word_ratio} format="pct" />
            </div>

            <div className="text-[11px] text-white/40 pt-2 border-t border-white/5">
              {f.word_count != null && <>Kelime: <b>{f.word_count}</b> · </>}
              {f.sentiment_score != null && <>Tonlama: <b>{f.sentiment_score.toFixed(2)}</b></>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Row({ icon: Icon, label, value }) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1.5">
        <span className="flex items-center gap-2 text-white/70"><Icon size={14} /> {label}</span>
        <span className="font-semibold">{((value ?? 0) * 100).toFixed(0)}%</span>
      </div>
      <Bar value={value} />
    </div>
  );
}

function Tag({ icon: Icon, label, value }) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/5 px-3 py-2.5">
      <div className="text-xs text-white/50 flex items-center gap-1.5"><Icon size={12} /> {label}</div>
      <div className="font-medium capitalize">{value || '—'}</div>
    </div>
  );
}

function Mini({ icon: Icon, label, value, format, inverse }) {
  const pct = Math.round((value ?? 0) * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <Icon size={12} className="text-white/40" />
      <span className="text-white/60 flex-1">{label}</span>
      <span className={`font-medium ${inverse ? (pct < 15 ? 'text-emerald-400' : pct < 35 ? 'text-amber-400' : 'text-red-400')
                                              : (pct > 60 ? 'text-emerald-400' : pct > 30 ? 'text-amber-400' : 'text-red-400')}`}>
        {pct}%
      </span>
    </div>
  );
}
