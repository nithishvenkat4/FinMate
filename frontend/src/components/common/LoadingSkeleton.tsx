import React from 'react';

export const StatCardSkeleton: React.FC = () => (
  <div className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs animate-pulse space-y-3">
    <div className="flex justify-between items-center">
      <div className="h-3 w-20 bg-slate-100 rounded-md" />
      <div className="w-8 h-8 rounded-xl bg-slate-100" />
    </div>
    <div className="h-7 w-28 bg-slate-200 rounded-md" />
    <div className="h-3 w-36 bg-slate-100 rounded-md" />
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="p-6 bg-white rounded-2xl border border-slate-200/80 shadow-xs animate-pulse space-y-4">
    <div className="flex justify-between">
      <div className="h-4 w-32 bg-slate-200 rounded-md" />
      <div className="h-4 w-20 bg-slate-100 rounded-md" />
    </div>
    <div className="space-y-3 pt-2">
      {Array.from({ length: rows }).map((_, idx) => (
        <div key={idx} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
          <div className="h-3 w-24 bg-slate-100 rounded-md" />
          <div className="h-3 w-40 bg-slate-100 rounded-md" />
          <div className="h-3 w-16 bg-slate-100 rounded-md" />
          <div className="h-3 w-20 bg-slate-200 rounded-md" />
        </div>
      ))}
    </div>
  </div>
);
