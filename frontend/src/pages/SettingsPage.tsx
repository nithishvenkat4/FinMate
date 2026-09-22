import React, { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Database, Server, Terminal, Shield, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await api.checkHealth();
      setHealth(res);
    } catch {
      setHealth({ status: 'offline', service: 'finmate-backend', database: 'disconnected' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 tracking-tight">System Settings & Health</h2>
        <p className="text-sm text-slate-400">
          Runtime status, database configuration, and developer environment controls.
        </p>
      </div>

      {/* Health Status Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Server className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-semibold text-slate-100">Backend API Connectivity</h3>
          </div>
          <button
            onClick={fetchHealth}
            className="p-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-slate-200"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Service Name</span>
            <span className="text-slate-200 font-semibold">{health?.service || 'finmate-backend'}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">API Status</span>
            <span
              className={`font-semibold ${
                health?.status === 'healthy' ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {health?.status || 'Unknown'}
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Database Connection</span>
            <span
              className={`font-semibold ${
                health?.database === 'connected' ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {health?.database || 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Developer CLI Commands */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-4">
        <div className="flex items-center gap-2.5">
          <Terminal className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-slate-100">Developer CLI & Data Management</h3>
        </div>

        <div className="space-y-3 text-xs">
          <div>
            <span className="text-slate-400 block mb-1">Seed Synthetic Demo Financial Dataset:</span>
            <code className="block p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-emerald-400 text-xs select-all">
              python scripts/seed_demo_data.py
            </code>
          </div>

          <div>
            <span className="text-slate-400 block mb-1">Run Automated Test Suite:</span>
            <code className="block p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-cyan-400 text-xs select-all">
              cd backend &amp;&amp; uv run pytest -v
            </code>
          </div>

          <div>
            <span className="text-slate-400 block mb-1">Launch Full Docker Compose Stack:</span>
            <code className="block p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-slate-300 text-xs select-all">
              docker compose up -d
            </code>
          </div>
        </div>
      </div>
    </div>
  );
};
