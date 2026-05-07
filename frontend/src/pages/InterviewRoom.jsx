import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, ChevronRight, Camera, Loader2, Gauge } from 'lucide-react';
import { interviews } from '../lib/api';
import { useWebcam } from '../hooks/useWebcam';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import ScorePanel from '../components/interview/ScorePanel.jsx';

const CATEGORY_TR = {
  behavioral: 'Davranışsal', technical: 'Teknik',
  system_design: 'Sistem Tasarımı', problem_solving: 'Problem Çözme',
  leadership: 'Liderlik', communication: 'İletişim', general: 'Genel',
};

function difficultyLabel(d) {
  if (d == null) return null;
  if (d < 0.4) return 'Kolay';
  if (d < 0.7) return 'Orta';
  return 'Zor';
}

export default function InterviewRoom() {
  const { id } = useParams();
  const nav = useNavigate();
  const { data: session, isLoading } = useQuery({
    queryKey: ['session', id], queryFn: () => interviews.get(id),
  });

  const { videoRef, streamRef, ready, error, captureFrameJpeg } = useWebcam();
  const { recording, start, stop } = useAudioRecorder(streamRef.current);

  const [idx, setIdx] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [busy, setBusy] = useState(false);
  const [lastScore, setLastScore] = useState(null);
  const questionShownAt = useRef(Date.now());

  const questions = session?.questions ?? [];
  const current = questions[idx];
  const isLast = idx >= questions.length - 1;

  // Yeni soruya geçtiğinde zamanlayıcıyı sıfırla
  useEffect(() => { questionShownAt.current = Date.now(); }, [idx, current?.id]);

  async function submit() {
    if (!current) return;
    setBusy(true);
    try {
      let audioBase64 = null;
      if (recording) audioBase64 = await stop();
      const frameBase64 = captureFrameJpeg();
      const responseTimeMs = Date.now() - questionShownAt.current;
      const score = await interviews.answer(id, {
        questionId: current.id, transcript, audioBase64, frameBase64, responseTimeMs,
      });
      setLastScore(score);
    } finally { setBusy(false); }
  }

  async function next() {
    setLastScore(null); setTranscript('');
    if (isLast) {
      await interviews.complete(id);
      nav(`/sessions/${id}`);
    } else {
      setIdx((i) => i + 1);
    }
  }

  if (isLoading) return <div className="card animate-pulse h-64" />;

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <div className="xl:col-span-2 space-y-5">
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs uppercase tracking-wider text-white/50">
              Soru {idx + 1} / {questions.length}
            </div>
            <div className="flex gap-2 text-xs">
              {current?.category && (
                <span className="px-2 py-1 rounded-md bg-white/5 border border-white/10">
                  {CATEGORY_TR[current.category] || current.category}
                </span>
              )}
              {current?.difficulty != null && (
                <span className="px-2 py-1 rounded-md bg-brand-500/15 border border-brand-500/30 text-brand-200 flex items-center gap-1">
                  <Gauge size={11} /> {difficultyLabel(current.difficulty)}
                </span>
              )}
              {current?.source === 'llm' && (
                <span className="px-2 py-1 rounded-md bg-accent-500/15 border border-accent-500/30 text-accent-400">
                  AI üretimi
                </span>
              )}
            </div>
          </div>
          <AnimatePresence mode="wait">
            <motion.h2
              key={current?.id}
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="text-2xl font-semibold leading-snug"
            >
              {current?.prompt}
            </motion.h2>
          </AnimatePresence>
        </div>

        <div className="card relative overflow-hidden p-0">
          {error ? (
            <div className="aspect-video grid place-items-center text-red-400 text-sm p-4">{error}</div>
          ) : (
            <video ref={videoRef} muted playsInline className="w-full aspect-video bg-black object-cover" />
          )}
          <div className="absolute top-3 left-3 flex gap-2 text-xs">
            <span className="px-2 py-1 rounded-md bg-black/50 backdrop-blur flex items-center gap-1">
              <Camera size={12} /> {ready ? 'canlı' : 'bağlanıyor'}
            </span>
            {recording && (
              <span className="px-2 py-1 rounded-md bg-red-500/80 flex items-center gap-1 animate-pulse">
                <Mic size={12} /> kayıt
              </span>
            )}
          </div>
        </div>

        <div className="card">
          <label className="label">Cevabın (yazılı)</label>
          <textarea
            className="input min-h-[120px]" value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Konuşurken cevabını buraya yaz…"
          />
          <div className="flex gap-2 mt-3">
            {!recording ? (
              <button className="btn-ghost" onClick={start} disabled={!ready}>
                <Mic size={14} /> Kaydı başlat
              </button>
            ) : (
              <button className="btn-ghost" onClick={stop}>
                <Square size={14} /> Durdur
              </button>
            )}
            <button className="btn-primary ml-auto" onClick={submit} disabled={busy || !transcript}>
              {busy ? <Loader2 size={14} className="animate-spin" /> : null}
              {busy ? 'Değerlendiriliyor…' : 'Cevabı gönder'}
            </button>
            {lastScore && (
              <button className="btn-primary" onClick={next}>
                {isLast ? 'Bitir' : 'Sonraki'} <ChevronRight size={14} />
              </button>
            )}
          </div>
        </div>
      </div>

      <ScorePanel score={lastScore} />
    </div>
  );
}
