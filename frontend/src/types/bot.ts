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
  coins_per_hour: number;
  last_round: number;
  last_round_xp: number;
}

export interface RoundHistoryItem {
  round: number;
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
  current_stage: string;
  rounds_played: number;
  mystery_boxes: number;
  uptime: string;
  box_counts: BoxCounts;
  coin_stats: CoinStats;
  round_history: RoundHistoryItem[];
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
