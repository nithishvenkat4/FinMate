/**
 * Central API Client for FinMate FastAPI Backend.
 */

import {
  AnalyticsSummary,
  DataQualitySummary,
  FinancialProfile,
  Goal,
  ImportSummaryResult,
  Investment,
  Transaction,
  TransactionCategory,
} from '../types';

const BASE_URL = '';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.error && errJson.error.message) {
        errorMsg = errJson.error.message;
      }
    } catch {
      // Ignore JSON parse error on non-json response
    }
    throw new Error(errorMsg);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Health
  checkHealth: () => request<{ status: string; service: string; database: string }>('/health'),

  // Analytics & Data Quality
  getAnalyticsSummary: () => request<AnalyticsSummary>('/api/v1/analytics/summary'),
  getDataQualitySummary: () => request<DataQualitySummary>('/api/v1/data-quality/summary'),

  // Categories
  getCategories: () => request<TransactionCategory[]>('/api/v1/categories'),
  createCategory: (data: { name: string; category_type: string; description?: string }) =>
    request<TransactionCategory>('/api/v1/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Transactions
  getTransactions: (params?: { transaction_type?: string; category?: string; page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.transaction_type) query.append('transaction_type', params.transaction_type);
    if (params?.category) query.append('category', params.category);
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());
    return request<{ items: Transaction[]; total: number; page: number; total_pages: number }>(
      `/api/v1/transactions?${query.toString()}`
    );
  },
  createTransaction: (data: Partial<Transaction>) =>
    request<Transaction>('/api/v1/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateTransaction: (id: string, data: Partial<Transaction>) =>
    request<Transaction>(`/api/v1/transactions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteTransaction: (id: string) =>
    request<{ message: string }>(`/api/v1/transactions/${id}`, {
      method: 'DELETE',
    }),

  // Goals
  getGoals: () => request<Goal[]>('/api/v1/goals'),
  createGoal: (data: Partial<Goal>) =>
    request<Goal>('/api/v1/goals', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateGoal: (id: string, data: Partial<Goal>) =>
    request<Goal>(`/api/v1/goals/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteGoal: (id: string) =>
    request<{ message: string }>(`/api/v1/goals/${id}`, {
      method: 'DELETE',
    }),

  // Investments
  getInvestments: () => request<Investment[]>('/api/v1/investments'),
  createInvestment: (data: Partial<Investment>) =>
    request<Investment>('/api/v1/investments', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteInvestment: (id: string) =>
    request<{ message: string }>(`/api/v1/investments/${id}`, {
      method: 'DELETE',
    }),

  // Profile
  getProfile: () => request<FinancialProfile>('/api/v1/profile'),
  updateProfile: (data: Partial<FinancialProfile>) =>
    request<FinancialProfile>('/api/v1/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // CSV Imports
  previewCsv: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<ImportSummaryResult>('/api/v1/imports/transactions/preview', {
      method: 'POST',
      body: formData,
    });
  },
  importCsv: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<ImportSummaryResult>('/api/v1/imports/transactions', {
      method: 'POST',
      body: formData,
    });
  },
};
