import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className = '',
}) => {
  return (
    <div
      className={`py-12 px-6 flex flex-col items-center text-center bg-white rounded-2xl border border-slate-200/80 shadow-xs ${className}`}
    >
      <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600 mb-3.5 shadow-xs">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-900 tracking-tight mb-1">{title}</h3>
      <p className="text-xs text-slate-500 max-w-md leading-relaxed mb-5">{description}</p>
      {(actionLabel || secondaryActionLabel) && (
        <div className="flex items-center gap-2.5">
          {secondaryActionLabel && onSecondaryAction && (
            <button
              onClick={onSecondaryAction}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 bg-slate-50 border border-slate-200 hover:bg-slate-100 hover:text-slate-800 transition"
            >
              {secondaryActionLabel}
            </button>
          )}
          {actionLabel && onAction && (
            <button
              onClick={onAction}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 shadow-xs transition"
            >
              {actionLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
