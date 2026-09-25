import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'emerald' | 'cyan' | 'amber' | 'purple' | 'rose' | 'teal' | 'slate';
  trend?: string;
}

const colorMap = {
  emerald: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-100',
    text: 'text-emerald-700',
    icon: 'text-emerald-600',
  },
  teal: {
    bg: 'bg-teal-50',
    border: 'border-teal-100',
    text: 'text-teal-700',
    icon: 'text-teal-600',
  },
  cyan: {
    bg: 'bg-sky-50',
    border: 'border-sky-100',
    text: 'text-sky-700',
    icon: 'text-sky-600',
  },
  amber: {
    bg: 'bg-amber-50',
    border: 'border-amber-100',
    text: 'text-amber-700',
    icon: 'text-amber-600',
  },
  purple: {
    bg: 'bg-purple-50',
    border: 'border-purple-100',
    text: 'text-purple-700',
    icon: 'text-purple-600',
  },
  rose: {
    bg: 'bg-rose-50',
    border: 'border-rose-100',
    text: 'text-rose-700',
    icon: 'text-rose-600',
  },
  slate: {
    bg: 'bg-slate-100',
    border: 'border-slate-200',
    text: 'text-slate-700',
    icon: 'text-slate-600',
  },
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'teal',
  trend,
}) => {
  const styles = colorMap[color] || colorMap.teal;

  return (
    <div className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs hover-lift transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-xl border ${styles.bg} ${styles.border} ${styles.icon}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="space-y-1">
        <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
        {(subtitle || trend) && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            {trend && <span className={`font-semibold ${styles.text}`}>{trend}</span>}
            {subtitle && <span>{subtitle}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
