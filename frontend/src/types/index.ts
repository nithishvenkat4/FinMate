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

// Phase 3 AI Models & Intelligence Types
export interface TransactionClassificationResult {
  predicted_category: string;
  confidence: number;
  requires_user_confirmation: boolean;
  contributing_tokens: string[];
  model_version: string;
  confidence_threshold: number;
}

export interface ExpenseForecastResult {
  predicted_expense: number | null;
  uncertainty_range?: {
    lower_bound: number;
    upper_bound: number;
    confidence_level: string;
    margin: number;
  };
  features_used?: Record<string, any>;
  model_version: string;
  limitation_notice: string;
}

export interface AnomalyCheckResult {
  is_unusual: boolean;
  anomaly_score: number;
  category: string;
  amount: number;
  ratio_to_benchmark: number;
  explanation: string;
  classification_notice: string;
}

export interface RAGRetrieveResult {
  query: string;
  retrieved_chunks: Array<{
    chunk_id: string;
    document_name: string;
    title: string;
    organization: string;
    reference_code: string;
    topic: string;
    similarity_score: number;
    text: string;
  }>;
  sources: Array<{
    title: string;
    organization: string;
    reference_code: string;
    topic: string;
    jurisdiction: string;
    document_name: string;
  }>;
  has_sufficient_evidence: boolean;
  notice?: string;
}

export interface AIAskResult {
  question: string;
  deterministic_facts: Record<string, any>;
  ml_forecast?: ExpenseForecastResult | null;
  rag_sources: Array<{
    title: string;
    organization: string;
    reference_code: string;
    topic: string;
    jurisdiction: string;
    document_name: string;
  }>;
  ai_decision_support: {
    summary: string;
    key_factors: string[];
    evidence_used: string[];
    uncertainties: string[];
    action_options: string[];
    user_decision_required: boolean;
    provider?: string;
  };
  safety_notice: string;
}

export interface ModelMetadataItem {
  task: string;
  model_name: string;
  version: string;
  algorithm: string;
  hyperparameters: Record<string, any>;
  metrics: Record<string, any>;
  is_selected: boolean;
  is_baseline: boolean;
  notes?: string;
  registered_at: string;
}

export interface ModelRegistryResult {
  models: ModelMetadataItem[];
  last_updated?: string;
}

// Phase 4 Multi-Agent Intelligence Types
export interface ExecutionStepItem {
  step_number: number;
  agent: string;
  action: string;
  tool?: string | null;
  status: string;
  detail: string;
  duration_ms: number;
}

export interface AgentApprovalItem {
  id: string;
  task_id: string;
  user_id: string;
  agent_name: string;
  action_type: string;
  target_id: string;
  current_value: Record<string, any>;
  proposed_value: Record<string, any>;
  reason: string;
  status: string;
  expires_at: string;
  created_at: string;
}

export interface AgentPendingApprovalPayload {
  approval_id: string;
  action_type: string;
  status: string;
  target_id: string;
  current_value: Record<string, any>;
  proposed_value: Record<string, any>;
  reason: string;
  expires_at: string;
  message: string;
}

export interface AgentTaskResult {
  task_id: string;
  status: 'pending' | 'running' | 'waiting_for_user' | 'completed' | 'failed' | 'cancelled';
  intent: string;
  summary: string;
  agents_used: string[];
  tools_used: string[];
  facts: Array<Record<string, any>>;
  predictions: Array<Record<string, any>>;
  recommendations: string[];
  tradeoffs: Array<Record<string, any>>;
  assumptions: string[];
  uncertainties: string[];
  sources: Array<Record<string, any>>;
  evidence_quality: string;
  execution_trace: ExecutionStepItem[];
  pending_approval?: AgentPendingApprovalPayload | null;
}

export interface AgentToolItem {
  name: string;
  description: string;
  allowed_agents: string[];
  is_mutation: boolean;
  requires_approval: boolean;
}

// Phase 5 Financial Decision & What-If Simulation Types
export type DecisionType =
  | 'purchase'
  | 'goal_contribution'
  | 'large_expense'
  | 'debt_payment'
  | 'saving'
  | 'investment'
  | 'subscription'
  | 'income_change'
  | 'expense_change'
  | 'custom';

export interface BaselineFinancialState {
  monthly_income: string | number;
  monthly_expenses: string | number;
  monthly_surplus: string | number;
  monthly_discretionary_spending?: string | number;
  current_savings: string | number;
  available_cash: string | number;
  savings_rate: string | number;
  emergency_buffer_months?: string | number | null;
  savings_coverage_months?: string | number | null;
  has_sufficient_data: boolean;
  notes: string[];
}

export interface FinancialImpact {
  new_savings: string | number;
  savings_change: string | number;
  new_monthly_surplus: string | number;
  surplus_change: string | number;
  new_monthly_expenses: string | number;
  expense_change: string | number;
  cash_position_change: string | number;
  projected_emergency_buffer_months?: string | number | null;
  savings_coverage_months?: string | number | null;
}

export interface GoalImpactDetail {
  goal_id: string;
  goal_name: string;
  target_amount: string | number;
  current_amount: string | number;
  remaining_amount: string | number;
  current_monthly_saving: string | number;
  required_monthly_saving: string | number;
  estimated_months_to_goal?: number | null;
  scenario_months_to_goal?: number | null;
  timeline_difference_months?: number | null;
  impact_summary: string;
}

export interface ScenarioResponse {
  id?: string | null;
  name: string;
  description?: string | null;
  assumptions: string[];
  financial_impact: FinancialImpact;
  goal_impact: GoalImpactDetail[];
  savings_impact: Record<string, any>;
  cash_flow_impact: Record<string, any>;
  timeline_impact: Record<string, any>;
  warnings: string[];
}

export interface DecisionExplanation {
  summary: string;
  what_changes: string[];
  what_stays_unchanged: string[];
  trade_off_analysis: string;
  key_considerations: string[];
}

export interface DecisionSimulateRequest {
  decision_type: DecisionType;
  amount: number | string;
  title: string;
  description?: string | null;
  category?: string | null;
  affected_goal_id?: string | null;
  custom_parameters?: Record<string, any>;
  save_to_history?: boolean;
}

export interface DecisionSimulationResponse {
  decision_id?: string | null;
  decision: {
    decision_type: string;
    title: string;
    description?: string | null;
    amount: string | number;
    category?: string | null;
    created_at?: string;
  };
  baseline: BaselineFinancialState;
  scenarios: ScenarioResponse[];
  explanation: DecisionExplanation;
  assumptions: string[];
  warnings: string[];
  data_limitations: string[];
}

export interface ScenarioCompareItem {
  metric: string;
  baseline: string;
  scenarios: Record<string, string>;
}

export interface ScenarioCompareResponse {
  title: string;
  comparison_matrix: ScenarioCompareItem[];
  scenarios_summary: Record<string, string>;
  trade_off_summary: string;
}

export interface DecisionListItem {
  id: string;
  user_id: string;
  decision_type: string;
  title: string;
  description?: string | null;
  amount: string | number;
  category?: string | null;
  status: string;
  scenario_count: number;
  created_at: string;
  goal_impact_summary?: string | null;
}

export interface DecisionDetailResponse {
  id: string;
  user_id: string;
  decision_type: string;
  title: string;
  description?: string | null;
  amount: string | number;
  category?: string | null;
  status: string;
  scenarios: ScenarioResponse[];
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}


