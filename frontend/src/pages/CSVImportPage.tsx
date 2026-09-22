import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  FileText,
  HelpCircle,
  Info,
  RefreshCw,
  UploadCloud,
  XCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { ImportSummaryResult } from '../types';
import { formatINR } from '../utils/formatters';

interface CSVImportPageProps {
  onImportSuccess?: () => void;
}

const SAMPLE_CSV = `date,description,amount,type,category,notes
2026-09-01,Salary,60000,income,Salary,Monthly salary
2026-09-02,Swiggy,450,expense,Food,Dinner
2026-09-03,Amazon,1200,expense,Shopping,Electronics
2026-09-04,Uber,300,expense,Transport,Cab
2026-09-05,Netflix,649,expense,Entertainment,Subscription
2026-09-06,Electricity,1800,expense,Utilities,Power bill
`;

export const CSVImportPage: React.FC<CSVImportPageProps> = ({ onImportSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewResult, setPreviewResult] = useState<ImportSummaryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [isPersisting, setIsPersisting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewResult(null);
      setSuccessMessage(null);
      setErrorMessage(null);
    }
  };

  const downloadSampleCsv = () => {
    const blob = new Blob([SAMPLE_CSV], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'finmate_sample_transactions.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePreview = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.previewCsv(selectedFile);
      setPreviewResult(res);
      if (res.errors && res.errors.length > 0) {
        setErrorMessage(res.errors.join(' '));
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to preview CSV file.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!selectedFile) return;
    setIsPersisting(true);
    setErrorMessage(null);
    try {
      const res = await api.importCsv(selectedFile);
      setSuccessMessage(
        `Successfully imported ${res.valid_rows} transactions into your FinMate account! (Batch ID: ${res.import_id.slice(0, 8)})`
      );
      setPreviewResult(res);
      if (onImportSuccess) onImportSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to import transactions.');
    } finally {
      setIsPersisting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight">CSV Transaction Ingestion</h2>
            <span className="text-xs uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Phase 2 Pipeline
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Upload, validate, normalize, and inspect financial transactions with automatic duplicate detection.
          </p>
        </div>

        <button
          onClick={downloadSampleCsv}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 text-slate-300 border border-slate-800 hover:border-slate-700 hover:text-white transition"
        >
          <Download className="w-4 h-4 text-emerald-400" />
          <span>Download Sample CSV</span>
        </button>
      </div>

      {/* Format Guidelines Card */}
      <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-2 text-xs text-slate-400">
        <div className="flex items-center gap-2 text-slate-300 font-semibold text-xs">
          <HelpCircle className="w-4 h-4 text-cyan-400" />
          <span>Supported CSV Column Structure</span>
        </div>
        <p>
          Your CSV file must include headers in the first row. FinMate will normalize whitespace, date formats (YYYY-MM-DD or DD/MM/YYYY), and currency symbols automatically.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
          <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-emerald-400 font-bold">date</span> (Required)
          </div>
          <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-emerald-400 font-bold">description</span> (Required)
          </div>
          <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-emerald-400 font-bold">amount</span> (Required &gt; 0)
          </div>
          <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-emerald-400 font-bold">type</span> (income / expense)
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="p-8 rounded-2xl border-2 border-dashed border-slate-800 bg-slate-900/30 hover:border-slate-700 transition text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto shadow-lg shadow-cyan-500/10">
          <UploadCloud className="w-7 h-7" />
        </div>

        <div>
          <label className="cursor-pointer">
            <span className="px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-600/20 transition inline-block">
              Choose CSV File
            </span>
            <input type="file" accept=".csv,text/csv" onChange={handleFileChange} className="hidden" />
          </label>
          <p className="text-xs text-slate-500 mt-2">Maximum file size: 5 MB • Standard UTF-8 encoding</p>
        </div>

        {selectedFile && (
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-slate-200">
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold">{selectedFile.name}</span>
            <span className="text-slate-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
          </div>
        )}

        {selectedFile && !previewResult && (
          <div className="pt-2">
            <button
              onClick={handlePreview}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-cyan-600 hover:bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-600/20 transition mx-auto"
            >
              {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
              <span>{loading ? 'Validating CSV...' : 'Validate & Preview CSV'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Error & Success Messages */}
      {errorMessage && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-300 text-xs flex items-center gap-3">
          <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 text-xs flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span className="font-medium">{successMessage}</span>
        </div>
      )}

      {/* Validation Preview Results */}
      {previewResult && (
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100">Data Quality & Validation Report</h3>
              <p className="text-xs text-slate-400 font-mono">File: {previewResult.filename}</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleConfirmImport}
                disabled={isPersisting || previewResult.valid_rows === 0}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-600/20 disabled:opacity-50 transition"
              >
                {isPersisting && <RefreshCw className="w-4 h-4 animate-spin" />}
                <span>Import {previewResult.valid_rows} Valid Rows to Database</span>
              </button>
            </div>
          </div>

          {/* Metrics summary banner */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xl font-bold text-slate-100 font-mono">{previewResult.total_rows}</div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider">Total Rows</div>
            </div>
            <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
              <div className="text-xl font-bold text-emerald-400 font-mono">{previewResult.valid_rows}</div>
              <div className="text-[10px] text-emerald-400 uppercase tracking-wider">Accepted / Valid</div>
            </div>
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20">
              <div className="text-xl font-bold text-amber-400 font-mono">{previewResult.warning_rows}</div>
              <div className="text-[10px] text-amber-400 uppercase tracking-wider">Review Warnings</div>
            </div>
            <div className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/20">
              <div className="text-xl font-bold text-rose-400 font-mono">{previewResult.invalid_rows}</div>
              <div className="text-[10px] text-rose-400 uppercase tracking-wider">Rejected / Malformed</div>
            </div>
            <div className="p-3 rounded-xl bg-cyan-500/5 border border-cyan-500/20">
              <div className="text-xl font-bold text-cyan-400 font-mono">{previewResult.duplicate_rows}</div>
              <div className="text-[10px] text-cyan-400 uppercase tracking-wider">Duplicate Flags</div>
            </div>
          </div>

          {/* Row-by-Row Preview Table */}
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800 sticky top-0 bg-slate-900 z-10">
                <tr>
                  <th className="py-2.5 px-3">Row #</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3 text-right">Amount</th>
                  <th className="py-2.5 px-3">Quality Flags & Diagnostics</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {previewResult.row_results.map((r) => {
                  const norm = r.normalized_data;
                  return (
                    <tr
                      key={r.row_number}
                      className={r.is_valid ? 'hover:bg-slate-800/30' : 'bg-rose-500/5 hover:bg-rose-500/10'}
                    >
                      <td className="py-2.5 px-3 font-mono text-slate-500">{r.row_number}</td>
                      <td className="py-2.5 px-3">
                        {r.is_valid ? (
                          r.issues.some((i) => i.severity === 'warning') ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              Warning
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Valid
                            </span>
                          )
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            Rejected
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {norm ? norm.transaction_date : r.raw_data.date || '-'}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-slate-200">
                        {norm ? norm.description : r.raw_data.description || '-'}
                      </td>
                      <td className="py-2.5 px-3 capitalize font-semibold text-[11px]">
                        {norm ? (
                          <span className={norm.transaction_type === 'income' ? 'text-emerald-400' : 'text-rose-400'}>
                            {norm.transaction_type}
                          </span>
                        ) : (
                          r.raw_data.type || '-'
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{norm ? norm.category : r.raw_data.category || '-'}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-200">
                        {norm ? formatINR(norm.amount) : r.raw_data.amount || '-'}
                      </td>
                      <td className="py-2.5 px-3">
                        {r.issues.length > 0 ? (
                          <div className="space-y-1">
                            {r.issues.map((iss, idx) => (
                              <div
                                key={idx}
                                className={`text-[10px] flex items-center gap-1 ${
                                  iss.severity === 'error'
                                    ? 'text-rose-400'
                                    : iss.severity === 'warning'
                                    ? 'text-amber-400'
                                    : 'text-cyan-400'
                                }`}
                              >
                                {iss.severity === 'error' ? (
                                  <AlertCircle className="w-3 h-3 shrink-0" />
                                ) : (
                                  <AlertTriangle className="w-3 h-3 shrink-0" />
                                )}
                                <span>{iss.message}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-[10px] text-slate-500 font-mono">Passed checks</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
