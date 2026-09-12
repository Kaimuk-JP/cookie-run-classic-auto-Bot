export interface BoxCounts {
  wood: number;
  silver: number;
  gold: number;
  rainbow: number;
  total: number;
}

export interface CoinStats {
  session_earned: number;
  session_xp_earned: number;
  lifetime_earned?: number;
  lifetime_xp_earned?: number;
  coins_per_hour: number;
  lifetime_coins_per_hour?: number;
  last_round: number;
  last_round_xp: number;
}

export interface RoundHistoryItem {
  round: number;
  session_round?: number;
  time: string;
  duration: string;
  score?: number;
  coins: number;
  xp: number;
  boxes: string[];
  box_count: number;
  has_screenshot: boolean;
  screenshot: string;
}

export interface CaptchaStats {
  total_attempts: number;
  success_count: number;
  fail_count: number;
  last_attempt_time?: string | null;
  last_result?: 'success' | 'fail' | null;
}

export interface HeartStats {
  running: boolean;
  rounds: number;
  success_count: number;
  current_step?: string;
}

export interface CleanerStats {
  running: boolean;
  is_busy: boolean;
  current_device?: string | null;
  current_step?: string;
  next_run?: string | null;
  next_run_seconds?: number;
}

export interface Device {
  serial: string;
  name: string;
  emu_name?: string;
  display_name?: string;
  model: string;
  status: string;
  index: number;
  port?: number | string;
  is_running: boolean;
  active_mode?: 'bot_engine' | 'heart_farmer' | 'friend_cleaner' | 'idle';
  activity_description?: string;
  current_stage: string;
  rounds_played: number;
  session_rounds?: number;
  mystery_boxes: number;
  session_mystery_boxes?: number;
  uptime: string;
  session_uptime?: string;
  total_uptime?: string;
  session_start_time?: string;
  box_counts: BoxCounts;
  session_box_counts?: BoxCounts;
  coin_stats: CoinStats;
  round_history: RoundHistoryItem[];
  session_round_history?: RoundHistoryItem[];
  captcha_stats?: CaptchaStats;
  heart_stats?: HeartStats;
  cleaner_stats?: CleanerStats;
}

export interface BotSettings {
  device_serial?: string;
  device_ip: string;
  device_port: number;
  use_hp_boost: boolean;
  use_item_extension: boolean;
  use_double_xp: boolean;
  use_fast_start: boolean;
  fast_start_min_stock: number;
  use_cookie_relay: boolean;
  cookie_relay_min_stock: number;
  use_desired_random_boost: boolean;
  desired_boost_id: string;
  detect_relic: boolean;
  send_friend_lives: boolean;
  heart_farmer_enabled?: boolean;
  heart_farmer_device?: string;
  heart_farmer_devices?: string[];
  heart_farmer_invite?: string;
  stop_goal_rounds_enabled: boolean;
  stop_goal_rounds_target: number;
  stop_goal_time_enabled: boolean;
  stop_goal_time_hours: number;
  auto_action_enabled?: boolean;
  auto_action_mode?: 'jump_only' | 'slide_only' | 'both';
  auto_action_interval?: number;
  macro_enabled?: boolean;
  selected_macro_id?: string;
}

export interface MacroAction {
  t: number;
  action: 'jump' | 'double_jump' | 'slide' | 'tap';
  air_time?: number;
  duration?: number;
  x?: number;
  y?: number;
}

export interface MacroProfile {
  id: string;
  name: string;
  description?: string;
  author?: string;
  created_at?: string;
  duration_seconds?: number;
  loop?: boolean;
  action_count?: number;
  actions?: MacroAction[];
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error' | 'bot' | 'adb' | 'farmer' | 'sys' | string;
  message: string;
  target?: string;
}

export interface DiscordSettings {
  webhook_url: string;
  enabled: boolean;
  notify_boxes: boolean;
  notify_antibot: boolean;
  notify_status: boolean;
  attach_screenshot: boolean;
}
