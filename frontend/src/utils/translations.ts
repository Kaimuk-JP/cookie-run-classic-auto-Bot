/**
 * แปลงชื่อ Stage และสถานะการทำงานจาก Bot Engine เป็นภาษาไทยทั้งหมด 100%
 */
export const translateStageToThai = (stageName?: string, isRunning?: boolean): string => {
  if (!stageName || stageName === 'IDLE' || stageName === 'None' || stageName === 'null') {
    return isRunning ? 'กำลังทำงาน...' : 'พร้อมทำงาน (หยุดพัก)';
  }

  const map: Record<string, string> = {
    IDLE: 'พร้อมทำงาน (หยุดพัก)',
    RUNNING: 'กำลังทำงาน...',
    STARTING: 'กำลังเริ่มระบบบอท...',
    START_BOT: 'กำลังเริ่มระบบบอท...',
    INITIALIZING: 'กำลังเตรียมความพร้อมระบบ...',
    STOPPING: 'กำลังหยุดการทำงาน...',
    STOPPED: 'หยุดการทำงานแล้ว',
    MAINMENU: 'หน้าล็อบบี้ / เมนูหลัก',
    LOBBY: 'หน้าล็อบบี้ (เตรียมตัว)',
    PURCHASE_ITEM: 'หน้าซื้อไอเทม / บูสต์',
    STAGE_PLAY: 'กำลังเข้าสู่เกม...',
    PLAY_GAME: 'กำลังเริ่มเกม...',
    GAME_START: 'กำลังวิ่ง (คุกกี้ตัวแรก)',
    STAGE_IN_GAME: 'กำลังวิ่งในเกม...',
    IN_GAME: 'กำลังวิ่งในเกม...',
    GAME_RELAY: 'กำลังวิ่ง (ผลัดที่ 2)',
    GAME_COMPLETE: 'สรุปผลจบรอบเกม',
    RESULT_SCREEN: 'สรุปผลจบรอบเกม',
    MYSTERY_BOX: 'รับกล่องปริศนา',
    CONGRATULATIONS: 'ยินดีด้วย (ผ่านภารกิจ)',
    LEVEL_UP: 'เลเวลอัป',
    SET_REWARD: 'รับรางวัลเซ็ตสมบัติ',
    PREVIOUS_RESULTS: 'ผลคะแนนรอบก่อนหน้า',
    ENTER_LEAGUE: 'เข้าสู่ลีก',
    LEAGUE_RESULTS: 'ผลคะแนนลีก',
    PREVIOUS_RANK_RESULTS: 'ผลจัดอันดับ',
    TOO_MANY_TREASURES: 'สมบัติเต็มคลัง',
    PARTY_RUN: 'โหมดปาร์ตี้รัน',
    GAME_SETTINGS: 'หน้าตั้งค่าเกม',
    OVERTAKE_BREAK_SCORE: 'ทำลายสถิติคะแนน',
    RELIC_COMPLETE: 'วัตถุโบราณครบเซ็ต',
    RELIC_CLAIM: 'รับชิ้นส่วนวัตถุโบราณ',
    DAILY_CHECKIN: 'รับของเช็คชื่อประจำวัน',
    DAILY_CHECKIN_BOOST_SET: 'รับเซ็ตบูสต์ประจำวัน',
    DAILY_TREASURE: 'รับสมบัติประจำวัน',
    DAILY_NEW: 'ปิดประกาศข่าวสาร',
    ANTI_BOT: '🛡️ แก้แคปซ่ากันบอท',
    HEART_FARMER: '💖 กำลังปั๊มหัวใจ',
    FRIEND_CLEANER: '💌 กำลังลบเพื่อนเวล 1',
    CONNECTION_LOST: '🔌 หลุดการเชื่อมต่อ (กำลังรีเซ็ต)',
    INACTIVE: '💤 หน้าจอหยุดนิ่ง (กำลังรีสตาร์ท)',
    RESTART_GAME: '🔄 กำลังรีสตาร์ทเกมใหม่',
    RECOVERY: 'กำลังกู้คืนระบบหน้าจอ...',
    UNKNOWN: 'กำลังสแกนหาหน้าจอ...',
    PRE_GAME: 'หน้าเตรียมตัวเข้าเกม',
    POST_GAME: 'หน้าสรุปผลหลังจบเกม',
    ONLINE: 'ออนไลน์พร้อมทำงาน',
    OFFLINE: 'ออฟไลน์ (ไม่ได้เชื่อมต่อ)',
    CONNECTING: 'กำลังเชื่อมต่ออีมูเลเตอร์...',
    UNAUTHORIZED: 'รอการยืนยันสิทธิ์ ADB บนจอ',
  };

  const clean = stageName.toUpperCase().trim();
  if (map[clean]) return map[clean];

  // ตรวจจับข้อความค้นหาหน้าจอ (Searching...)
  if (clean.includes('SEARCHING')) {
    if (clean.includes('PRE_GAME')) return 'กำลังค้นหาหน้าล็อบบี้/เตรียมตัว...';
    if (clean.includes('IN_GAME')) return 'กำลังวิ่งในเกม (สแกนจังหวะ)...';
    if (clean.includes('POST_GAME')) return 'กำลังรอหน้าจอสรุปผล...';
    return 'กำลังสแกนหาหน้าจอ...';
  }

  if (clean.includes('PRE_GAME')) return 'หน้าเตรียมตัวเข้าเกม';
  if (clean.includes('IN_GAME')) return 'กำลังวิ่งในเกม...';
  if (clean.includes('POST_GAME')) return 'หน้าสรุปผลหลังจบเกม';

  // If already in Thai
  if (/[\u0E00-\u0E7F]/.test(stageName)) {
    return stageName;
  }

  return isRunning ? 'กำลังทำงาน...' : 'พร้อมทำงาน (หยุดพัก)';
};
