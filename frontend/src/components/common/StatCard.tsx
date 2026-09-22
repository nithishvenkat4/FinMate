import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'emerald' | 'cyan' | 'amber' | 'purple' | 'rose' | 'slate';
  trend?: string;
}

const colorMap = {
  emerald: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    text: 'text-emerald-400',
    glow: 'group-hover:border-emerald-500/40',
  },
  cyan: {
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/20',
    text: 'text-cyan-400',
    glow: 'group-hover:border-cyan-500/40',
  },
  amber: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    text: 'text-amber-400',
    glow: 'group-hover:border-amber-500/40',
  },
  purple: {
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
    text: 'text-purple-400',
    glow: 'group-hover:border-purple-500/40',
  },
  rose: {
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/20',
    text: 'text-rose-400',
    glow: 'group-hover:border-rose-500/40',
  },
  slate: {
    bg: 'bg-slate-800/40',
    border: 'border-slate-800',
    text: 'text-slate-300',
    glow: 'group-hover:border-slate-700',
  },
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'emerald',
  trend,
}) => {
  const styles = colorMap[color];

  return (
    <div
      className={`group relative p-5 rounded-2xl border bg-slate-900/70 backdrop-blur-sm transition-all duration-200 ${styles.border} ${styles.glow}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2.5 rounded-xl border ${styles.bg} ${styles.border} ${styles.text}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="space-y-1">
        <div className="text-2xl font-bold text-slate-100 tracking-tight">{value}</div>
        {(subtitle || trend) && (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {trend && <span className={`font-semibold ${styles.text}`}>{trend}</span>}
            {subtitle && <span>{subtitle}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
