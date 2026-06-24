export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  locale: string;
}

export interface CooperativeSettings {
  currency: string;
  default_operation_cost: string;
  stock_alerts_enabled: boolean;
  expiry_alerts_enabled: boolean;
  safety_alerts_enabled: boolean;
  expiry_alert_days: number;
  display_name: string;
  tagline: string;
  primary_color: string;
  logo_emoji: string;
  brand_name: string;
  agents_enabled: boolean;
  traceability_enabled: boolean;
}

export interface Cooperative {
  id: string;
  name: string;
  slug: string;
  tax_id: string;
  country: string;
  region: string;
  is_active: boolean;
  role: string | null;
  settings: CooperativeSettings | null;
  created_at: string;
}

export interface Campaign {
  id: string;
  label: string;
  start_date: string | null;
  end_date: string | null;
  is_closed: boolean;
  crops_count: number;
  created_at: string;
}

export interface Farm {
  id: string;
  owner: string;
  name: string;
  description: string;
  parcels_count: number;
  created_at: string;
}

export interface Parcel {
  id: string;
  farm: string;
  farm_name: string;
  name: string;
  sigpac_ref: string;
  area_ha: string;
  soil_type: string;
  latitude: string | null;
  longitude: string | null;
  polygon: unknown;
  is_active: boolean;
  created_at: string;
}

export interface Sector {
  id: string;
  parcel: string;
  parcel_name: string;
  name: string;
  area_ha: string;
  color: string;
  polygon: number[][] | null;
  crops_count: number;
  created_at: string;
}

export interface Crop {
  id: string;
  parcel: string;
  parcel_name: string;
  sector: string | null;
  species: string;
  variety: string;
  campaign: string;
  season: string | null;
  season_label: string | null;
  sowing_date: string | null;
  expected_harvest_date: string | null;
  status: string;
  expected_yield_kg: string | null;
  created_at: string;
}

export interface HarvestRecord {
  id: string;
  crop: string;
  crop_label: string;
  date: string;
  quantity_kg: string;
  quality_grade: string;
  price_per_kg: string | null;
  notes: string;
  created_at: string;
}

export interface FieldOperation {
  id: string;
  crop: string;
  operation_type: string;
  operation_type_display: string;
  date: string;
  description: string;
  area_ha: string | null;
  performed_by: string;
  created_at: string;
}

export interface Treatment {
  id: string;
  operation: string | null;
  crop: string;
  crop_label: string;
  product: string;
  product_name: string;
  date: string;
  dose: string;
  dose_unit: string;
  total_quantity: string | null;
  target_pest: string;
  weather: string;
  applicator: string;
  safety_interval_ok: boolean;
  created_at: string;
}

export interface Product {
  id: string;
  name: string;
  registration_number: string;
  active_ingredient: string;
  category: string;
  unit: string;
  safety_interval_days: number;
  reorder_level: string;
  unit_cost: string;
  current_stock: string;
  needs_reorder: boolean;
  created_at: string;
}

export interface StockBatch {
  id: string;
  product: string;
  product_name: string;
  lot: string;
  expiry_date: string | null;
  received_date: string | null;
  quantity: string;
  is_expired: boolean;
  created_at: string;
}

export interface StockMovement {
  id: string;
  product: string;
  product_name: string;
  batch: string | null;
  movement_type: string;
  quantity: string;
  signed_quantity: string;
  reason: string;
  treatment: string | null;
  created_at: string;
}

export interface CostEntry {
  id: string;
  crop: string;
  crop_label: string;
  category: string;
  category_display: string;
  source: string;
  amount: string;
  date: string;
  description: string;
  treatment: string | null;
  operation: string | null;
  created_by: string | null;
  created_at: string;
}

export interface ProfitabilityReport {
  id: string;
  crop: string;
  crop_label: string;
  total_cost: string;
  income: string;
  profit: string;
  cost_per_ha: string;
  margin_pct: string;
  computed_at: string;
}

export interface AlertRule {
  id: string;
  name: string;
  trigger: string;
  trigger_display: string;
  condition: Record<string, unknown>;
  severity: string;
  is_active: boolean;
  created_at: string;
}

export interface Alert {
  id: string;
  rule: string | null;
  trigger: string;
  trigger_display: string;
  severity: string;
  title: string;
  message: string;
  context: Record<string, unknown>;
  dedupe_key: string;
  acknowledged: boolean;
  resolved: boolean;
  created_at: string;
}

export interface TraceEvent {
  id: string;
  sequence: number;
  actor: string | null;
  actor_email: string | null;
  entity_type: string;
  entity_id: string;
  action: string;
  payload: Record<string, unknown>;
  occurred_at: string;
  prev_hash: string;
  hash: string;
}

export interface AuditLog {
  id: string;
  event: string;
  event_display: string;
  email: string;
  user: string | null;
  cooperative: string | null;
  ip_address: string | null;
  user_agent: string;
  detail: string;
  created_at: string;
}

export interface MfaDevice {
  id: string;
  name: string;
  confirmed: boolean;
  created_at: string;
}

export interface DashboardData {
  cooperative: string;
  role: string;
  counts: {
    farms: number;
    parcels: number;
    crops: number;
    total_area_ha: string;
  };
  production: {
    total_harvest_kg: string;
  };
  economics: {
    total_cost: string;
    total_income: string;
    total_profit: string;
  };
  alerts: {
    open: number;
    low_stock_products: number;
  };
  crops_by_status: { status: string; count: number }[];
}

export interface Agent {
  id: string;
  agent_type: string;
  name: string;
  purpose: string;
  skills: string[];
  tools: string[];
  is_active: boolean;
}

export interface AgentMessage {
  id: string;
  role: string;
  content: string;
  tool_name: string;
  created_at: string;
}

export interface AgentRun {
  id: string;
  agent: string;
  agent_name: string;
  status: string;
  input_text: string;
  output_text: string;
  messages: AgentMessage[];
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}
