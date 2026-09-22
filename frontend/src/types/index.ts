export interface Transaction {
  id: string;
  user_id: string;
  category_id?: string;
  transaction_date: string;
  description: string;
  amount: string | number;
  transaction_type: 'income' | 'expense';
  category: string;
  notes?: string;
  source_type: 'manual' | 'csv_import' | 'synthetic';
  source_reference?: string;
  import_id?: string;
  data_quality_flags?: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionCategory {
  id: string;
  name: string;
  category_type: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export interface Goal {
  id: string;
  user_id: string;
  name: string;
  target_amount: string | number;
  current_amount: string | number;
  target_date: string;
  priority: 'low' | 'medium' | 'high';
  progress_percentage: string | number;
  created_at: string;
  updated_at: string;
}

export interface Investment {
  id: string;
  user_id: string;
  asset_name: string;
  investment_type: string;
  quantity: string | number;
  current_value: string | number;
  created_at: string;
  updated_at: string;
}

export interface FinancialProfile {
  id: string;
  user_id: string;
  monthly_income: string | number;
  monthly_fixed_expenses: string | number;
  current_savings: string | number;
  risk_preference: 'conservative' | 'moderate' | 'aggressive';
  created_at: string;
  updated_at: string;
}

export interface CategorySpendingItem {
  category: string;
  total_amount: string | number;
  percentage: string | number;
  transaction_count: number;
}

export interface AnalyticsSummary {
  total_income: string | number;
  total_expenses: string | number;
  net_savings: string | number;
  savings_rate: string | number;
  transaction_count: number;
  profile_monthly_income?: string | number;
  profile_monthly_fixed_expenses?: string | number;
  profile_current_savings?: string | number;
  active_goals_count: number;
  total_investments_value: string | number;
  category_breakdown: CategorySpendingItem[];
}

export interface DataQualitySummary {
  total_transactions: number;
  valid_transactions: number;
  warning_transactions: number;
  invalid_transactions: number;
  possible_duplicates: number;
  missing_categories: number;
  future_transactions: number;
  high_value_transactions: number;
  total_income: string | number;
  total_expenses: string | number;
}

export interface QualityIssue {
  severity: 'error' | 'warning' | 'info';
  rule_code: string;
  message: string;
  field?: string;
}

export interface RowValidationResult {
  row_number: number;
  raw_data: Record<string, string>;
  normalized_data?: {
    transaction_date: string;
    description: string;
    amount: string | number;
    transaction_type: string;
    category: string;
    notes?: string;
  };
  is_valid: boolean;
  is_duplicate_candidate: boolean;
  issues: QualityIssue[];
}

export interface ImportSummaryResult {
  import_id: string;
  filename: string;
  source_type: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  warning_rows: number;
  duplicate_rows: number;
  status: string;
  errors: string[];
  row_results: RowValidationResult[];
}
