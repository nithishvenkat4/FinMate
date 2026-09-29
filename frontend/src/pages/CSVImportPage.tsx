import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Check,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  HelpCircle,
  RefreshCw,
  UploadCloud,
  XCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { ImportSummaryResult } from '../types';
import { formatINR } from '../utils/formatters';

interface CSVImportPageProps {
  onImportSuccess?: () => void;
  onNavigateTab?: (tab: any) => void;
}

const SAMPLE_CSV = `date,description,amount,type,category,notes
2026-09-01,Salary,60000,income,Salary,Monthly salary
2026-09-02,Swiggy,450,expense,Food,Dinner
2026-09-03,Amazon,1200,expense,Shopping,Electronics
2026-09-04,Uber,300,expense,Transport,Cab
2026-09-05,Netflix,649,expense,Entertainment,Subscription
2026-09-06,Electricity,1800,expense,Utilities,Power bill
`;

const SAMPLE_BANK_CSV = `Txn Date,Description,Cheque No,Debit Amount,Credit Amount,Balance
2026-09-01,Monthly Salary Credit,REF98124,,65000.00,125000.00
2026-09-02,Swiggy Takeout,UPI-84920,450.00,,124550.00
2026-09-03,Amazon Shopping,CHQ88192,1200.00,,123350.00
2026-09-04,House Rent Transfer,NEFT-4912,15000.00,,108350.00
2026-09-05,Electricity Bill,BILL-9321,1800.00,,106550.00
2026-09-06,Consulting Dividend,REF3819,,12000.00,118550.00
`;

export const CSVImportPage: React.FC<CSVImportPageProps> = ({
  onImportSuccess,
  onNavigateTab,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewResult, setPreviewResult] = useState<ImportSummaryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [isPersisting, setIsPersisting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Workflow current step: 1: Select -> 2: Check -> 3: Review -> 4: Done
  const currentStep = successMessage ? 4 : previewResult ? 3 : selectedFile ? 2 : 1;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewResult(null);
      setSuccessMessage(null);
      setErrorMessage(null);
    }
  };

  const downloadSampleCsv = (isBank: boolean = false) => {
    const csvContent = isBank ? SAMPLE_BANK_CSV : SAMPLE_CSV;
    const filename = isBank ? 'bank_statement_sample.csv' : 'finmate_sample_transactions.csv';
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
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
      setErrorMessage(err.message || 'Failed to inspect CSV file.');
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
        `Successfully imported ${res.valid_rows} transactions into your FinMate account!`
      );
      setPreviewResult(res);
      if (onImportSuccess) onImportSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to import transactions.');
    } finally {
      setIsPersisting(false);
    }
  };

  const steps = [
    { num: 1, title: 'Select File' },
    { num: 2, title: 'Check Your File' },
    { num: 3, title: 'Review Transactions' },
    { num: 4, title: 'Import Complete' },
  ];

  return (
    <div className="space-y-6 animate-fadeIn max-w-5xl">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Import Transactions</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Upload CSV bank statements or export files to add multiple transactions at once.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadSampleCsv(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200 hover:bg-teal-100 shadow-xs transition"
            title="Download Bank Statement format with Txn Date, Description, Cheque No, Debit Amount, Credit Amount, Balance"
          >
            <Download className="w-3.5 h-3.5 text-teal-600" />
            <span>Bank Statement Template</span>
          </button>
          <button
            onClick={() => downloadSampleCsv(false)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-xs transition"
            title="Download Standard Ledger format (Date, Description, Amount, Type, Category)"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Standard Template</span>
          </button>
        </div>
      </div>

      {/* 4-Step Visual Progress Stepper */}
      <div className="p-4 rounded-2xl border border-slate-200/80 bg-white shadow-xs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {steps.map((st) => {
            const isCompleted = currentStep > st.num;
            const isCurrent = currentStep === st.num;
            return (
              <div
                key={st.num}
                className={`flex items-center gap-2.5 p-2 rounded-xl ${
                  isCurrent
                    ? 'bg-teal-50/70 border border-teal-100 text-teal-900'
                    : isCompleted
                    ? 'text-slate-800'
                    : 'text-slate-400'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${
                    isCompleted
                      ? 'bg-teal-600 text-white'
                      : isCurrent
                      ? 'bg-teal-600 text-white'
                      : 'bg-slate-100 text-slate-500 border border-slate-200'
                  }`}
                >
                  {isCompleted ? <Check className="w-3.5 h-3.5" /> : st.num}
                </div>
                <span className="text-xs font-medium truncate">{st.title}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Format Guidelines Card */}
      <div className="p-4 rounded-2xl border border-slate-200/80 bg-slate-50/60 space-y-3 text-xs text-slate-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-800 font-semibold text-xs">
            <HelpCircle className="w-4 h-4 text-teal-600" />
            <span>Supported CSV Column Formats</span>
          </div>
          <span className="text-[11px] font-medium text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-100">
            Auto-Detects Comma (,) &amp; Tab (\t) Separators
          </span>
        </div>
        <p className="text-[11px] text-slate-500">
          FinMate automatically cleans currency symbols (₹, $, commas), detects standard Indian date formats (DD-MMM-YYYY, DD/MM/YYYY, YYYY-MM-DD), and supports both netbanking statement exports and standard ledger CSVs.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          {/* Format 1: Bank Statement */}
          <div className="p-3 rounded-xl bg-white border border-teal-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-teal-900 text-xs">Option A: Bank Statement Export</span>
              <span className="text-[10px] bg-teal-50 text-teal-700 px-1.5 py-0.5 rounded font-mono font-medium">Netbanking Default</span>
            </div>
            <div className="flex flex-wrap gap-1 font-mono text-[10px]">
              <span className="px-2 py-1 rounded bg-teal-50 text-teal-800 border border-teal-100">Txn Date</span>
              <span className="px-2 py-1 rounded bg-teal-50 text-teal-800 border border-teal-100">Description</span>
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-600 border border-slate-200">Cheque No</span>
              <span className="px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-100 font-semibold">Debit Amount</span>
              <span className="px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-100 font-semibold">Credit Amount</span>
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-600 border border-slate-200">Balance</span>
            </div>
            <p className="text-[10px] text-slate-400">
              * Debit amounts are logged as expenses; Credit amounts as income. Cheque No &amp; Balance are tracked automatically.
            </p>
          </div>

          {/* Format 2: Standard Ledger */}
          <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800 text-xs">Option B: Standard Ledger</span>
              <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono font-medium">Generic CSV</span>
            </div>
            <div className="flex flex-wrap gap-1 font-mono text-[10px]">
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-700 border border-slate-200 font-semibold">date</span>
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-700 border border-slate-200 font-semibold">description</span>
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-700 border border-slate-200 font-semibold">amount</span>
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-700 border border-slate-200 font-semibold">type (income/expense)</span>
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-500 border border-slate-200">category</span>
              <span className="px-2 py-1 rounded bg-slate-50 text-slate-500 border border-slate-200">notes</span>
            </div>
            <p className="text-[10px] text-slate-400">
              * Ideal for custom spreadsheets and exports where type is in a dedicated column.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Drop Zone */}
      <div className="p-8 rounded-2xl border-2 border-dashed border-slate-200 bg-white hover:border-teal-400 hover:bg-slate-50/40 transition text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-100 text-teal-600 flex items-center justify-center mx-auto shadow-xs">
          <UploadCloud className="w-6 h-6" />
        </div>

        <div>
          <label className="cursor-pointer">
            <span className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition inline-block">
              Choose CSV File
            </span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
          <p className="text-[11px] text-slate-400 mt-2">Maximum file size: 5 MB • Standard UTF-8 encoding</p>
        </div>

        {selectedFile && (
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700">
            <FileSpreadsheet className="w-4 h-4 text-teal-600" />
            <span className="font-semibold">{selectedFile.name}</span>
            <span className="text-slate-500">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
          </div>
        )}

        {selectedFile && !previewResult && (
          <div className="pt-2">
            <button
              onClick={handlePreview}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-900 text-white shadow-xs transition mx-auto"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{loading ? 'Checking file...' : 'Review & Verify Transactions'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Error & Success Messages */}
      {errorMessage && (
        <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs flex items-center gap-3">
          <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-5 rounded-2xl border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs space-y-3">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span className="font-semibold text-sm">{successMessage}</span>
          </div>
          <p className="text-[11px] text-emerald-700 pl-7">
            Your transactions have been recorded. You can view them in the ledger or return to your overview.
          </p>
          <div className="flex gap-2.5 pt-1 pl-7">
            {onNavigateTab && (
              <>
                <button
                  onClick={() => onNavigateTab('transactions')}
                  className="px-4 py-2 rounded-xl font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition"
                >
                  View in Transactions
                </button>
                <button
                  onClick={() => onNavigateTab('dashboard')}
                  className="px-4 py-2 rounded-xl font-medium bg-white text-emerald-800 border border-emerald-200 hover:bg-emerald-100/50 transition"
                >
                  Return to Dashboard
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Review Transactions Report */}
      {previewResult && !successMessage && (
        <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Review Transactions</h3>
              <p className="text-xs text-slate-500 font-mono">File: {previewResult.filename}</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleConfirmImport}
                disabled={isPersisting || previewResult.valid_rows === 0}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs disabled:opacity-50 transition"
              >
                {isPersisting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>Import {previewResult.valid_rows} Transactions</span>
              </button>
            </div>
          </div>

          {/* Validation Metrics Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-lg font-bold text-slate-900 font-mono">{previewResult.total_rows}</div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">
                Total Rows
              </div>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200">
              <div className="text-lg font-bold text-emerald-700 font-mono">{previewResult.valid_rows}</div>
              <div className="text-[10px] text-emerald-700 uppercase tracking-wider font-medium">
                Ready to Import
              </div>
            </div>
            <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200">
              <div className="text-lg font-bold text-amber-700 font-mono">
                {previewResult.warning_rows}
              </div>
              <div className="text-[10px] text-amber-700 uppercase tracking-wider font-medium">
                Review Warnings
              </div>
            </div>
            <div className="p-3 rounded-xl bg-rose-50/70 border border-rose-200">
              <div className="text-lg font-bold text-rose-700 font-mono">
                {previewResult.invalid_rows}
              </div>
              <div className="text-[10px] text-rose-700 uppercase tracking-wider font-medium">
                Invalid
              </div>
            </div>
            <div className="p-3 rounded-xl bg-sky-50/70 border border-sky-200">
              <div className="text-lg font-bold text-sky-700 font-mono">
                {previewResult.duplicate_rows}
              </div>
              <div className="text-[10px] text-sky-700 uppercase tracking-wider font-medium">
                Duplicates
              </div>
            </div>
          </div>

          {/* Row-by-Row Review Table */}
          <div className="overflow-x-auto max-h-96 rounded-xl border border-slate-100">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200 sticky top-0 bg-slate-50 z-10 font-medium">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3 text-right">Amount</th>
                  <th className="py-2.5 px-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {previewResult.row_results.map((r) => {
                  const norm = r.normalized_data;
                  return (
                    <tr
                      key={r.row_number}
                      className={
                        r.is_valid
                          ? 'hover:bg-slate-50/80'
                          : 'bg-rose-50/30 hover:bg-rose-50/60'
                      }
                    >
                      <td className="py-2.5 px-3 font-mono text-slate-400">{r.row_number}</td>
                      <td className="py-2.5 px-3">
                        {r.is_valid ? (
                          r.issues.some((i) => i.severity === 'warning') ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                              Warning
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Valid
                            </span>
                          )
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            Invalid
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-600 whitespace-nowrap">
                        {norm ? norm.transaction_date : r.raw_data.date || '—'}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-slate-800">
                        {norm ? norm.description : r.raw_data.description || '—'}
                      </td>
                      <td className="py-2.5 px-3 capitalize font-semibold text-[11px]">
                        {norm ? (
                          <span
                            className={
                              norm.transaction_type === 'income'
                                ? 'text-emerald-700'
                                : 'text-rose-700'
                            }
                          >
                            {norm.transaction_type}
                          </span>
                        ) : (
                          r.raw_data.type || '—'
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">
                        {norm ? norm.category : r.raw_data.category || '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-800">
                        {norm ? formatINR(norm.amount) : r.raw_data.amount || '—'}
                      </td>
                      <td className="py-2.5 px-3">
                        {r.issues.length > 0 ? (
                          <div className="space-y-1">
                            {r.issues.map((iss, idx) => (
                              <div
                                key={idx}
                                className={`text-[10px] flex items-center gap-1 ${
                                  iss.severity === 'error'
                                    ? 'text-rose-600'
                                    : iss.severity === 'warning'
                                    ? 'text-amber-600'
                                    : 'text-slate-600'
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
                          <span className="text-[10px] text-slate-400">Passed checks</span>
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
