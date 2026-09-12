import { Device, BotSettings, DiscordSettings, LogEntry } from '../types/bot';

export const botApi = {
  async getDevices(): Promise<Device[]> {
    const res = await fetch('/api/devices');
    if (!res.ok) throw new Error('Failed to fetch devices');
    return res.json();
  },

  async startBot(serial: string, settings?: Partial<BotSettings>): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`/api/start?device=${encodeURIComponent(serial)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: serial, device_serial: serial, ...(settings || {}) }),
    });
    return res.json();
  },

  async stopBot(serial: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`/api/stop?device=${encodeURIComponent(serial)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device: serial, device_serial: serial }),
      });
      return await res.json();
    } catch {
      return { success: true, message: `สั่งหยุดจอ ${serial} ทันทีเรียบร้อยแล้ว` };
    }
  },

  async startAllBots(): Promise<{ success: boolean; message: string; results: Record<string, any> }> {
    const res = await fetch('/api/start-all', { method: 'POST' });
    return res.json();
  },

  async stopAllBots(): Promise<{ success: boolean; message: string; results?: Record<string, any> }> {
    try {
      const res = await fetch('/api/stop-all', { method: 'POST' });
      return await res.json();
    } catch {
      return { success: true, message: 'สั่งหยุดทุกจอทันทีเรียบร้อยแล้ว' };
    }
  },

  async clearRam(): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/clear-ram', { method: 'POST' });
    return res.json();
  },

  async resetApp(serial: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/reset-app', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: serial }),
    });
    return res.json();
  },

  async testConnection(serial: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: serial }),
    });
    return res.json();
  },

  async resetStats(device?: string): Promise<{ success: boolean; message: string }> {
    const devQuery = device ? `?device=${encodeURIComponent(device)}` : '';
    const res = await fetch(`/api/reset-stats${devQuery}`, {
      method: 'POST',
    });
    return res.json();
  },

  async getSettings(serial: string): Promise<BotSettings> {
    const res = await fetch(`/api/settings?device=${encodeURIComponent(serial)}`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async saveSettings(serial: string, settings: BotSettings): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`/api/settings?device=${encodeURIComponent(serial)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return res.json();
  },

  async tapScreen(serial: string, x: number, y: number): Promise<void> {
    await fetch('/api/tap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device: serial, device_serial: serial, x, y }),
    });
  },

  async getLogs(serial?: string): Promise<LogEntry[]> {
    const url = serial && serial !== 'all' ? `/api/logs?device=${encodeURIComponent(serial)}` : '/api/logs';
    const res = await fetch(url);
    if (!res.ok) return [];
    return res.json();
  },

  async getDiscordSettings(): Promise<DiscordSettings> {
    const res = await fetch('/api/discord');
    if (!res.ok) throw new Error('Failed to fetch Discord settings');
    return res.json();
  },

  async saveDiscordSettings(settings: DiscordSettings): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/discord', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return res.json();
  },

  async testDiscordWebhook(url: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/discord/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ webhook_url: url }),
    });
    return res.json();
  },

  async startFarmer(params: { device?: string; devices?: string[]; invite_url?: string }): Promise<{ success: boolean; message: string; results?: any[] }> {
    const res = await fetch('/api/farmer/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  async stopFarmer(params?: { device?: string; devices?: string[] }): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch('/api/farmer/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params || {}),
      });
      return await res.json();
    } catch {
      return { success: true, message: 'สั่งหยุดระบบปั้มหัวใจทันทีเรียบร้อยแล้ว' };
    }
  },

  async getFarmerStatus(device?: string): Promise<any> {
    const devQuery = device && device !== 'all' ? `?device=${encodeURIComponent(device)}` : '';
    const res = await fetch(`/api/farmer/status${devQuery}`);
    if (!res.ok) return { running: false, rounds: 0, any_running: false };
    return res.json();
  },

  async startFriendCleaner(params: { device?: string; devices?: string[]; interval_minutes?: number; run_immediately?: boolean }): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/cleaner/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  async stopFriendCleaner(): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/cleaner/stop', {
      method: 'POST',
    });
    return res.json();
  },

  async runOnceFriendCleaner(device?: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/cleaner/run_once', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device }),
    });
    return res.json();
  },

  async getCleanerStatus(): Promise<any> {
    const res = await fetch('/api/cleaner/status');
    if (!res.ok) return { is_running: false };
    return res.json();
  }
};
