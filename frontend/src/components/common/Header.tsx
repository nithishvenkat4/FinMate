import React from 'react';
import { Menu, RefreshCw, Search, Sparkles, User } from 'lucide-react';

interface HeaderProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
  onToggleMobileSidebar?: () => void;
  onNavigateTab?: (tab: any) => void;
}

export const Header: React.FC<HeaderProps> = ({
  onRefresh,
  isRefreshing,
  onToggleMobileSidebar,
  onNavigateTab,
}) => {
  return (
    <header className="h-16 border-b border-slate-200/80 bg-white/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        {/* Mobile menu button */}
        {onToggleMobileSidebar && (
          <button
            onClick={onToggleMobileSidebar}
            className="md:hidden p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        {/* Brand identity */}
        <div
          onClick={() => onNavigateTab && onNavigateTab('dashboard')}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-xs group-hover:bg-teal-700 transition">
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 tracking-tight text-lg">FinMate</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-100 hidden sm:inline-block">
                Personal Finance
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block -mt-0.5">Financial Decision Support</p>
          </div>
        </div>
      </div>

      {/* Global Quick Action / Search bar */}
      <div className="hidden lg:flex items-center flex-1 max-w-md mx-8">
        <div
          onClick={() => onNavigateTab && onNavigateTab('ai-advisor')}
          className="w-full flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 hover:border-slate-300 text-slate-400 text-xs cursor-pointer transition"
        >
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span className="flex-1 text-slate-500">Ask FinMate a question or search...</span>
          <span className="flex items-center gap-1 text-[11px] font-medium text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-100">
            <Sparkles className="w-3 h-3 text-teal-600" />
            Ask
          </span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-xl border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 hover:border-slate-300 transition shadow-xs"
            title="Refresh financial data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-teal-600' : ''}`} />
          </button>
        )}

        {/* User Profile Pill */}
        <div
          onClick={() => onNavigateTab && onNavigateTab('profile')}
          className="flex items-center gap-2.5 pl-3 border-l border-slate-200 cursor-pointer group"
        >
          <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-200 group-hover:border-teal-300 transition">
            <User className="w-4 h-4 text-slate-600" />
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-semibold text-slate-800 leading-tight">Demo User</p>
            <p className="text-[11px] text-slate-500 leading-tight">Personal Account</p>
          </div>
        </div>
      </div>
    </header>
  );
};
