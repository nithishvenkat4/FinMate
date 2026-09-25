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

  // Phase 3 AI Intelligence APIs
  classifyTransaction: (data: { description: string; amount?: number | string; transaction_type?: string }) =>
    request<import('../types').TransactionClassificationResult>('/api/v1/ai/classify-transaction', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  forecastExpenses: (data: { recent_lags?: number[]; forecast_month?: number } = {}) =>
    request<import('../types').ExpenseForecastResult>('/api/v1/ai/forecast-expenses', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  checkAnomaly: (data: { amount: number | string; category: string; is_weekend?: boolean }) =>
    request<import('../types').AnomalyCheckResult>('/api/v1/ai/anomaly-check', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  retrieveGuidance: (query: string, top_k: number = 3) =>
    request<import('../types').RAGRetrieveResult>('/api/v1/ai/retrieve', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    }),
  askFinMate: (question: string, include_financial_context: boolean = true) =>
    request<import('../types').AIAskResult>('/api/v1/ai/ask', {
      method: 'POST',
      body: JSON.stringify({ question, include_financial_context }),
    }),
  getModelRegistry: () =>
    request<import('../types').ModelRegistryResult>('/api/v1/ai/models'),

  // Phase 4 Multi-Agent Intelligence APIs
  createAgentTask: (query: string, user_id?: string) =>
    request<import('../types').AgentTaskResult>('/api/v1/agent/tasks', {
      method: 'POST',
      body: JSON.stringify({ query, user_id }),
    }),
  getAgentTask: (taskId: string) =>
    request<import('../types').AgentTaskResult>(`/api/v1/agent/tasks/${taskId}`),
  getAgentTrace: (taskId: string) =>
    request<import('../types').ExecutionStepItem[]>(`/api/v1/agent/tasks/${taskId}/trace`),
  getPendingApprovals: () =>
    request<import('../types').AgentApprovalItem[]>('/api/v1/agent/approvals/pending'),
  approveAgentAction: (taskId: string, approvalId: string) =>
    request<{ approval_id: string; task_id: string; status: string; message: string }>(
      `/api/v1/agent/tasks/${taskId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({ approval_id: approvalId }),
      }
    ),
  rejectAgentAction: (taskId: string, approvalId: string) =>
    request<{ approval_id: string; task_id: string; status: string; message: string }>(
      `/api/v1/agent/tasks/${taskId}/reject`,
      {
        method: 'POST',
        body: JSON.stringify({ approval_id: approvalId }),
      }
    ),
  cancelAgentTask: (taskId: string) =>
    request<{ task_id: string; status: string; message: string }>(
      `/api/v1/agent/tasks/${taskId}/cancel`,
      { method: 'POST' }
    ),
  getAgentTools: () =>
    request<import('../types').AgentToolItem[]>('/api/v1/agent/tools'),
};

