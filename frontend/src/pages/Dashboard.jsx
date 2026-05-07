import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';
import { Activity, TrendingUp, CheckCircle2, Sparkles } from 'lucide-react';
import { analytics } from '../lib/api';

const CATEGORY_TR = {
  behavioral: 'Davranışsal', technical: 'Teknik',
  system_design: 'Sistem', problem_solving: 'Problem',
  leadership: 'Liderlik', communication: 'İletişim', general: 'Genel',
};

const Stat = ({ icon: Icon, label, value, hint }) => (
  <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="card">
    <div className="flex items-center gap-2 text-white/60 text-sm">
      <Icon size={14} /> {label}
    </div>
    <div className="text-3xl font-semibold mt-2">{value}</div>
    {hint && <div className="text-xs text-white/40 mt-1">{hint}</div>}
  </motion.div>
);

export default function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: analytics.dashboard });

  if (isLoading) return <Skeleton />;
  const trend = data?.trend ?? [];
  const emo = Object.entries(data?.emotionDistribution ?? {}).map(([name, count]) => ({ name, count }));
  const skill = (data?.skillProfile ?? []).map((s) => ({
    category: CATEGORY_TR[s.category] || s.category,
    level: Math.round(s.level * 100),
    samples: s.samples,
  }));

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <div className="text-xs uppercase tracking-wider text-white/50">Genel Bakış</div>
          <h1 className="text-3xl font-semibold mt-1">Panel</h1>
        </div>
        <div className="flex items-center gap-2 text-sm text-white/60">
          <Sparkles size={14} className="text-brand-400" />
          Sistem her cevabınla birlikte öğreniyor
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Stat icon={Activity} label="Toplam oturum" value={data?.totalSessions ?? 0} />
        <Stat icon={CheckCircle2} label="Tamamlanan" value={data?.completedSessions ?? 0} />
        <Stat icon={TrendingUp} label="Ortalama puan"
              value={(data?.averageScore ?? 0).toFixed(2)}
              hint="Cevap kalitesi ve özgüvenin ortalaması" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <div className="text-sm text-white/60 mb-3">Puan trendi</div>
          <div className="h-64">
            <ResponsiveContainer>
              <LineChart data={trend}>
                <CartesianGrid stroke="rgba(255,255,255,.06)" />
                <XAxis dataKey="date" hide />
                <YAxis domain={[0, 1]} stroke="rgba(255,255,255,.4)" fontSize={12} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,.1)' }} />
                <Line type="monotone" dataKey="score" stroke="#818cf8" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-white/60 mb-3">Yetenek profili (kategori bazında)</div>
          <div className="h-64">
            {skill.length === 0 ? (
              <div className="h-full grid place-items-center text-white/40 text-sm">
                Birkaç mülakat tamamladıkça burada güçlü ve zayıf yönlerin oluşacak.
              </div>
            ) : (
              <ResponsiveContainer>
                <RadarChart data={skill} outerRadius="80%">
                  <PolarGrid stroke="rgba(255,255,255,.1)" />
                  <PolarAngleAxis dataKey="category" tick={{ fill: 'rgba(255,255,255,.6)', fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,.3)', fontSize: 10 }} />
                  <Radar dataKey="level" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.35} />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,.1)' }} />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="card lg:col-span-2">
          <div className="text-sm text-white/60 mb-3">Duygu dağılımı</div>
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={emo}>
                <CartesianGrid stroke="rgba(255,255,255,.06)" />
                <XAxis dataKey="name" stroke="rgba(255,255,255,.4)" fontSize={12} />
                <YAxis stroke="rgba(255,255,255,.4)" fontSize={12} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,.1)' }} />
                <Bar dataKey="count" fill="#22d3ee" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="grid grid-cols-3 gap-4">
      {[1, 2, 3].map((i) => <div key={i} className="card animate-pulse h-28" />)}
    </div>
  );
}
