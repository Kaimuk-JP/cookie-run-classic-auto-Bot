/**
 * แปลงชื่อ Stage จาก Bot Engine เป็นภาษาไทยที่เข้าใจง่าย
 */
export const translateStageToThai = (stageName?: string, isRunning?: boolean): string => {
  if (!stageName || stageName === 'IDLE' || stageName === 'None') {
    return isRunning ? 'กำลังทำงาน...' : 'พร้อมทำงาน (หยุดพัก)';
  }

  const map: Record<string, string> = {
    IDLE: 'พร้อมทำงาน (หยุดพัก)',
    RUNNING: 'กำลังทำงาน...',
    START_BOT: 'กำลังเริ่มระบบบอท...',
    MAINMENU: 'หน้าเมนูหลัก',
    LOBBY: 'หน้าเตรียมตัวเริ่มเกม',
    GAME_START: 'กำลังวิ่ง (ตัวแรก)',
    GAME_RELAY: 'กำลังวิ่ง (ผลัดสอง)',
    GAME_COMPLETE: 'สรุปผลจบรอบเกม',
    MYSTERY_BOX: 'รับกล่องปริศนา',
    CONGRATULATIONS: 'หน้ายินดีด้วย',
    LEVEL_UP: 'เลเวลอัป',
    SET_REWARD: 'รับรางวัลเซ็ต',
    PREVIOUS_RESULTS: 'ผลคะแนนรอบก่อนหน้า',
    ENTER_LEAGUE: 'เข้าสู่ลีก',
    LEAGUE_RESULTS: 'ผลคะแนนลีก',
    PREVIOUS_RANK_RESULTS: 'ผลจัดอันดับ',
    TOO_MANY_TREASURES: 'สมบัติเต็มคลัง',
    PARTY_RUN: 'โหมดปาร์ตี้รัน',
    OVERTAKE_BREAK_SCORE: 'ทำลายสถิติคะแนน',
    RELIC_COMPLETE: 'วัตถุโบราณครบเซ็ต',
    RELIC_CLAIM: 'รับชิ้นส่วนวัตถุโบราณ',
    DAILY_CHECKIN: 'รับของเช็คชื่อประจำวัน',
    DAILY_CHECKIN_BOOST_SET: 'รับเซ็ตบูสต์ประจำวัน',
    DAILY_TREASURE: 'รับสมบัติประจำวัน',
    DAILY_NEW: 'ปิดประกาศข่าวสาร',
    PURCHASE_ITEM: 'กำลังซื้อไอเทม',
    ANTI_BOT: '🛡️ ตรวจพบ Anti-Bot (กำลังแก้)',
    HEART_FARMER: '💖 กำลังปั๊มหัวใจ',
    FRIEND_CLEANER: '💌 กำลังลบเพื่อนเวล 1',
    RESTART_GAME: '🔄 กำลังรีสตาร์ทเกมใหม่',
    RECOVERY: 'กำลังตรวจหาหน้าจอ...',
    UNKNOWN: 'กำลังสแกนหาหน้าจอ...',
  };

  const clean = stageName.toUpperCase().trim();
  if (map[clean]) return map[clean];

  // If already in Thai
  if (/[\u0E00-\u0E7F]/.test(stageName)) {
    return stageName;
  }

  return stageName;
};
