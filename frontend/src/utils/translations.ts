/**
 * แปลงชื่อ Stage และสถานะการทำงานจาก Bot Engine เป็นภาษาไทยทั้งหมด 100%
 */
export const translateStageToThai = (stageName?: string, isRunning?: boolean): string => {
  if (!stageName || stageName === 'IDLE' || stageName === 'None' || stageName === 'null') {
    return isRunning ? 'กำลังทำงาน...' : 'พร้อมทำงาน';
  }

  const map: Record<string, string> = {
    IDLE: 'พร้อมทำงาน',
    RUNNING: 'กำลังทำงาน...',
    STARTING: 'กำลังเริ่มบอท...',
    START_BOT: 'กำลังเริ่มบอท...',
    INITIALIZING: 'กำลังเตรียมระบบ...',
    STOPPING: 'กำลังหยุด...',
    STOPPED: 'หยุดแล้ว',
    MAINMENU: 'หน้าล็อบบี้',
    LOBBY: 'หน้าล็อบบี้',
    PURCHASE_ITEM: 'ซื้อไอเทม',
    STAGE_PLAY: 'กำลังเข้าเกม...',
    PLAY_GAME: 'กำลังเริ่มเกม...',
    GAME_START: 'วิ่งผลัดแรก',
    STAGE_IN_GAME: 'กำลังวิ่ง...',
    IN_GAME: 'กำลังวิ่ง...',
    GAME_RELAY: 'วิ่งผลัดสอง',
    GAME_COMPLETE: 'สรุปผลเกม',
    RESULT_SCREEN: 'สรุปผลเกม',
    MYSTERY_BOX: 'รับกล่อง',
    CONGRATULATIONS: 'ผ่านภารกิจ',
    LEVEL_UP: 'เลเวลอัป',
    SET_REWARD: 'รับรางวัลสมบัติ',
    PREVIOUS_RESULTS: 'คะแนนรอบก่อน',
    ENTER_LEAGUE: 'เข้าลีก',
    LEAGUE_RESULTS: 'คะแนนลีก',
    PREVIOUS_RANK_RESULTS: 'ผลอันดับ',
    TOO_MANY_TREASURES: 'สมบัติเต็ม',
    PARTY_RUN: 'ปาร์ตี้รัน',
    GAME_SETTINGS: 'ตั้งค่าเกม',
    OVERTAKE_BREAK_SCORE: 'สถิติใหม่',
    RELIC_COMPLETE: 'วัตถุโบราณครบ',
    RELIC_CLAIM: 'รับวัตถุโบราณ',
    DAILY_CHECKIN: 'เช็คชื่อรายวัน',
    DAILY_CHECKIN_BOOST_SET: 'บูสต์รายวัน',
    DAILY_TREASURE: 'สมบัติรายวัน',
    DAILY_NEW: 'ปิดข่าวสาร',
    ANTI_BOT: '🛡️ แก้แคปซ่า',
    HEART_FARMER: '💖 ปั๊มหัวใจ',
    FRIEND_CLEANER: '💌 ลบเพื่อน',
    CONNECTION_LOST: '🔌 หลุดการเชื่อมต่อ',
    INACTIVE: '💤 หน้าจอนิ่ง',
    RESTART_GAME: '🔄 รีสตาร์ทเกม',
    RECOVERY: 'กู้คืนหน้าจอ...',
    UNKNOWN: 'สแกนหน้าจอ...',
    PRE_GAME: 'เตรียมเข้าเกม',
    POST_GAME: 'สรุปผลเกม',
    ONLINE: 'ออนไลน์',
    OFFLINE: 'ออฟไลน์',
    CONNECTING: 'เชื่อมต่อ Emulator...',
    UNAUTHORIZED: 'รอสิทธิ์ ADB',
  };

  const clean = stageName.toUpperCase().trim();
  if (map[clean]) return map[clean];

  // ตรวจจับข้อความค้นหาหน้าจอ (Searching...)
  if (clean.includes('SEARCHING')) {
    if (clean.includes('PRE_GAME')) return 'ค้นหาล็อบบี้...';
    if (clean.includes('IN_GAME')) return 'กำลังวิ่ง...';
    if (clean.includes('POST_GAME')) return 'รอสรุปผล...';
    return 'สแกนหน้าจอ...';
  }

  if (clean.includes('PRE_GAME')) return 'เตรียมเข้าเกม';
  if (clean.includes('IN_GAME')) return 'กำลังวิ่ง...';
  if (clean.includes('POST_GAME')) return 'สรุปผลเกม';

  // If already in Thai
  if (/[\u0E00-\u0E7F]/.test(stageName)) {
    return stageName;
  }

  return isRunning ? 'กำลังทำงาน...' : 'พร้อมทำงาน';
};
