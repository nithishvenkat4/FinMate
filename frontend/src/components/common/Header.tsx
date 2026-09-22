import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertTriangle, User, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';

interface HeaderProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, isRefreshing }) => {
  const [health, setHealth] = useState<'healthy' | 'offline' | 'checking'>('checking');

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.checkHealth();
        if (res.status === 'healthy') {
          setHealth('healthy');
        } else {
          setHealth('offline');
        }
      } catch {
        setHealth('offline');
      }
    };
    check();
    const timer = setInterval(check, 10000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-400 flex items-center justify-center font-bold text-slate-950 text-lg shadow-lg shadow-emerald-500/20">
          F
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-slate-100 tracking-tight text-lg">FinMate</h1>
            <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Decision Support
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">Personal Financial Decision Agent • Phase 2</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend Status indicator */}
        <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border border-slate-800 bg-slate-900/90">
          <span
            className={`w-2 h-2 rounded-full animate-pulse ${
              health === 'healthy' ? 'bg-emerald-400' : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-300 font-medium">
            {health === 'healthy' ? 'API Online' : health === 'offline' ? 'API Disconnected' : 'Checking...'}
          </span>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition"
            title="Refresh financial data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        )}

        {/* User Pill */}
        <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 border border-slate-700">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden md:block text-left">
            <p className="text-xs font-medium text-slate-200">Demo User</p>
            <p className="text-[10px] text-slate-500">demo@finmate.local</p>
          </div>
        </div>
      </div>
    </header>
  );
};
