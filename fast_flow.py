"""
fast_flow.py - ระบบตรวจจับภาพความเร็วสูง (Dynamic Image Polling)
เร็วขึ้น 2 เท่า: ไม่ใช้ sleep ยาว แต่ตรวจจับรูปหน้าจอแบบเรียลไทม์ (ทุก 0.3-0.5 วิ)
เมื่อหน้าจอหรือปุ่มปรากฏจะกดทันทีอย่างแม่นยำจนจบกระบวนการ
"""
import sys, os, time, random, string
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

sys.path.insert(0, r'd:\bot cK\CookieRun_Bot_Ready_To_Share\CookieRun_Bot\src')
from adb import _run_cmd, get_adb_path, _format_target, device_capture_screen
import cv2, numpy as np

DEVICE = '127.0.0.1:16480'
PACKAGE = 'com.devsisters.crg'
INVITE_URL = 'https://cookierunglobal.onelink.me/Xr0A/onm0jzbf'
adb_path = get_adb_path()

OUT_DIR = r'C:\Users\kaimuk\.gemini\antigravity-ide\brain\ff2c24cc-56b6-49c2-87ef-5f70c5e8a215\screenshots\fast_run'
os.makedirs(OUT_DIR, exist_ok=True)

shot_counter = [0]
def cap(label):
    shot_counter[0] += 1
    img = device_capture_screen(DEVICE)
    if img is not None:
        p = os.path.join(OUT_DIR, f"{shot_counter[0]:03d}_{label}.png")
        cv2.imwrite(p, img)
    return img

def adb(*args, timeout=15):
    return _run_cmd([adb_path, '-s', _format_target(DEVICE)] + list(args),
                    capture_output=True, text=True, timeout=timeout)

def tap(x, y, delay=0.3):
    adb('shell', 'input', 'tap', str(x), str(y))
    if delay > 0:
        time.sleep(delay)

def keyevent(code, delay=0.2):
    adb('shell', 'input', 'keyevent', str(code))
    if delay > 0:
        time.sleep(delay)

def type_text(text):
    adb('shell', 'input', 'text', text)

def wait_until(condition_fn, timeout=30, interval=0.35, desc=""):
    """วนลูปตรวจสอบภาพหน้าจอแบบความเร็วสูง เจอแล้วทำต่อทันที"""
    if desc:
        print(f"  [รอ] {desc} (timeout {timeout}s)...", flush=True)
    deadline = time.time() + timeout
    t0 = time.time()
    while time.time() < deadline:
        img = device_capture_screen(DEVICE)
        if img is not None:
            res = condition_fn(img)
            if res:
                elapsed = time.time() - t0
                print(f"  ⚡ เจอ {desc} ใน {elapsed:.1f}s!", flush=True)
                return res, img
        time.sleep(interval)
    print(f"  ⚠️ Timeout รอ {desc}", flush=True)
    return None, None

# =========================================================================
# ฟังก์ชันตรวจสอบรูปแต่ละหน้าจอ
# =========================================================================

def check_age_popup(img):
    if img is None or float(img.mean()) > 180:
        return False
    # ตรวจปุ่ม Confirm สีส้ม (x: 500..780, y: 360..450) และการ์ดสีขาว
    roi_btn = img[360:450, 500:780]
    mask_btn = (roi_btn[:, :, 2] > 200) & (roi_btn[:, :, 1] > 80) & (roi_btn[:, :, 1] < 150) & (roi_btn[:, :, 0] < 80)
    roi_card = img[260:350, 500:780]
    return mask_btn.sum() > 2000 and float(roi_card.mean()) > 220

def check_tos_popup(img):
    if img is None or float(img.mean()) > 180:
        return False
    roi_card = img[260:350, 500:780]
    roi_btn = img[360:450, 500:780]
    mask_orange = (roi_btn[:, :, 2] > 200) & (roi_btn[:, :, 1] > 80) & (roi_btn[:, :, 1] < 150) & (roi_btn[:, :, 0] < 80)
    return float(roi_card.mean()) > 220 and mask_orange.sum() < 500 and float(roi_btn.mean()) > 200

def check_devplay_login_btn(img):
    if img is None: return False
    # ตรวจปุ่ม DevPlay Login สีส้ม (x: 400..650, y: 580..660)
    roi = img[580:660, 400:650]
    mask = (roi[:, :, 2] > 180) & (roi[:, :, 1] > 70) & (roi[:, :, 1] < 160) & (roi[:, :, 0] < 80)
    return mask.sum() > 4000

def check_email_signin_btn(img):
    if img is None: return False
    # ตรวจปุ่ม 'Sign in with E-mail' สีส้ม (x: 650..950, y: 350..430)
    roi = img[350:430, 650:950]
    mask = (roi[:, :, 2] > 200) & (roi[:, :, 1] > 80) & (roi[:, :, 1] < 150) & (roi[:, :, 0] < 80)
    return mask.sum() > 2500

def check_email_input_page(img):
    if img is None: return False
    # ตรวจสอบว่าหน้าจอ WebView กรอกอีเมลโหลดเสร็จสมบูรณ์ 100%
    # 1. ข้อความหัวเรื่อง 'Please enter your e-mail address' (y: 110..150, x: 410..750)
    roi_title = img[110:150, 410:750]
    gray_title = cv2.cvtColor(roi_title, cv2.COLOR_BGR2GRAY)
    dark_title = int((gray_title < 100).sum())

    # 2. หัวเว็บ 'CookieRun' (y: 50..80, x: 580..700)
    roi_header = img[50:80, 580:700]
    gray_header = cv2.cvtColor(roi_header, cv2.COLOR_BGR2GRAY)
    dark_header = int((gray_header < 100).sum())

    # ข้อความหัวเรื่องและหัวเว็บต้องปรากฏชัดเจน (ไม่ใช่จอขาวว่างเปล่า)
    return 300 < dark_title < 2500 and dark_header > 200

def check_password_input_page(img):
    if img is None: return False
    # หน้ากรอกรหัสผ่าน (มี 2 ช่อง + checkbox agree + Cloudflare)
    roi_title = img[100:160, 410:750]
    gray_title = cv2.cvtColor(roi_title, cv2.COLOR_BGR2GRAY)
    dark_title = int((gray_title < 100).sum())
    # ตรวจสอบว่ามีช่องกรอกรหัสช่องที่ 2 (y: 240..290)
    roi_box2 = img[240:290, 411:869]
    gray_box2 = cv2.cvtColor(roi_box2, cv2.COLOR_BGR2GRAY)
    box2_border = int(((gray_box2 < 210) & (gray_box2 > 150)).sum())
    return dark_title > 2500 or box2_border > 200

def check_cloudflare_green(img):
    # กล่อง checkbox Cloudflare ที่ (x: 410..460, y: 385..425)
    roi = img[385:425, 410:460]
    mask = (roi[:, :, 1] > 120) & (roi[:, :, 0] < 80) & (roi[:, :, 2] < 80)
    return mask.sum() > 50

def check_intro_video(img):
    # วิดีโอเริ่มเล่น (ไม่ใช่หน้าโหลดสีขาวหรือจอดำสนิท)
    br = float(img.mean())
    return 20 < br < 170

def check_quit_watching_popup(img):
    if img is None: return False
    # ตรวจปุ่ม Confirm สีเขียวบนหน้าต่าง 'Quit watching?' อยู่ฝั่งขวา (x: 650..930, y: 410..510)
    roi_c = img[410:510, 650:930]
    hsv_c = cv2.cvtColor(roi_c, cv2.COLOR_BGR2HSV)
    mask_c = cv2.inRange(hsv_c, (35, 100, 100), (85, 255, 255))
    # ตรวจปุ่ม Cancel สีเทาบนหน้าต่าง 'Quit watching?' อยู่ฝั่งซ้าย (x: 350..550, y: 410..510)
    roi_cancel = img[410:510, 350:550]
    mask_cancel = (np.abs(roi_cancel[:, :, 0].astype(int) - roi_cancel[:, :, 1].astype(int)) < 15) & \
                  (np.abs(roi_cancel[:, :, 1].astype(int) - roi_cancel[:, :, 2].astype(int)) < 15) & \
                  (roi_cancel[:, :, 0] > 90) & (roi_cancel[:, :, 0] < 160)
    return bool(mask_c.sum() > 2000 and mask_cancel.sum() > 2000)

def check_hi_there_popup(img):
    if img is None: return False
    # ตรวจปุ่ม Confirm สีเขียวบนหน้าต่าง 'Hi there!' อยู่ตรงกลางจอ (x: 550..700, y: 430..510)
    roi = img[430:510, 550:700]
    mask = (roi[:, :, 1] > 130) & (roi[:, :, 0] < 90) & (roi[:, :, 1] > roi[:, :, 0] * 1.5)
    # ต้องไม่มีปุ่ม Cancel สีเทาฝั่งซ้าย (ไม่ใช่ Quit watching?)
    roi_cancel = img[410:510, 350:550]
    mask_cancel = (np.abs(roi_cancel[:, :, 0].astype(int) - roi_cancel[:, :, 1].astype(int)) < 15) & \
                  (np.abs(roi_cancel[:, :, 1].astype(int) - roi_cancel[:, :, 2].astype(int)) < 15) & \
                  (roi_cancel[:, :, 0] > 90) & (roi_cancel[:, :, 0] < 160)
    return bool(mask.sum() > 3000 and mask_cancel.sum() < 1000)

def check_in_tutorial_room(img):
    if img is None: return False
    # ต้องไม่ใช่หน้าต่าง Quit watching? หรือ Hi there! เด็ดขาด
    if check_quit_watching_popup(img) or check_hi_there_popup(img):
        return False
    # ตรวจปุ่ม Jump (x: 50..230, y: 580..710)
    roi_jump = img[580:710, 50:230]
    return float(roi_jump.mean()) > 25

def is_tutorial_pause_menu(img):
    """ตรวจว่าเปิด Pause Menu ขึ้นมาจริงหรือยัง (Continue เขียวบน + Quit ฟ้าล่าง)"""
    if img is None: return False
    c_roi = img[380:460, 480:780]
    cyan = (c_roi[:, :, 0] > 120) & (c_roi[:, :, 1] > 120) & (c_roi[:, :, 2] < 70)
    g_roi = img[220:300, 480:780]
    green = (g_roi[:, :, 1] > 140) & (g_roi[:, :, 2] > 140) & (g_roi[:, :, 0] < 80)
    return cyan.sum() > 1000 and green.sum() > 1000

def is_tutorial_confirm_quit_dialog(img):
    """ตรวจว่าเปิดหน้าต่าง 'Quit the tutorial?' ขึ้นมาจริงหรือยัง (Quit ฟ้าบน + Cancel เทาล่าง)"""
    if img is None: return False
    c_roi = img[340:420, 480:780]
    cyan = (c_roi[:, :, 0] > 120) & (c_roi[:, :, 1] > 120) & (c_roi[:, :, 2] < 70)
    g_roi = img[490:560, 480:780]
    grey = (np.abs(g_roi[:, :, 0].astype(int) - g_roi[:, :, 1].astype(int)) < 15) & \
           (np.abs(g_roi[:, :, 1].astype(int) - g_roi[:, :, 2].astype(int)) < 15) & \
           (g_roi[:, :, 0] > 100) & (g_roi[:, :, 0] < 180)
    return cyan.sum() > 1000 and grey.sum() > 1000

def check_select_mode_popup(img):
    """ตรวจจับหน้าต่าง 'Select a Mode' (Party Run) ที่มีริบบิ้นม่วงบน และปุ่ม X เทากลมที่ (1215, 95)"""
    if img is None: return False
    roi_title = img[60:125, 400:880]
    purple = (roi_title[:, :, 0] > 110) & (roi_title[:, :, 2] > 90) & (roi_title[:, :, 1] < 70)
    roi_x = img[65:125, 1180:1250]
    white_x = (roi_x[:, :, 0] > 200) & (roi_x[:, :, 1] > 200) & (roi_x[:, :, 2] > 200)
    return purple.sum() > 600 and white_x.sum() > 30

def check_banner_or_news_popup(img):
    """ตรวจจับหน้าต่างข่าวสาร/ประกาศ/แนะนำฟีเจอร์ทั้งหมด ที่มีปุ่ม X เทากลมที่ (1125, 75)"""
    if img is None: return False
    btn_roi = img[50:95, 1105:1145]
    grey = (np.abs(btn_roi[:, :, 0].astype(int) - btn_roi[:, :, 1].astype(int)) < 15) & \
           (np.abs(btn_roi[:, :, 1].astype(int) - btn_roi[:, :, 2].astype(int)) < 15) & \
           (btn_roi[:, :, 0] > 90) & (btn_roi[:, :, 0] < 170)
    white = (btn_roi[:, :, 0] > 200) & (btn_roi[:, :, 1] > 200) & (btn_roi[:, :, 2] > 200)
    return bool(grey.sum() > 400 and white.sum() > 100)

def check_set_nickname_popup(img):
    if img is None: return False
    # ต้องไม่ใช่หน้าต่าง Quit watching? หรือ Hi there! เด็ดขาด
    if check_quit_watching_popup(img) or check_hi_there_popup(img):
        return False

    # 1. เช็คแถบพิมพ์ Android IME บาร์สีขาวด้านบน (Enter your nickname!)
    top_bar = img[35:85, 20:1260]
    if top_bar.mean() > 180:
        return True
        
    # 2. เช็คตัวการ์ดหน้าต่าง Set Nickname กลางจอ (x: 450..830, y: 200..340)
    card = img[200:340, 450:830]
    b, g, r = card[:, :, 0], card[:, :, 1], card[:, :, 2]
    is_grey_card = (np.abs(b.astype(int) - g.astype(int)) < 20) & \
                   (np.abs(g.astype(int) - r.astype(int)) < 20) & \
                   (g > 70) & (g < 230)
                   
    # 3. เช็คปุ่ม Confirm เดี่ยวตรงกลาง (x: 550..720, y: 440..530)
    btn = img[440:530, 550:720]
    btn_g = btn[:, :, 1]
    btn_b = btn[:, :, 0]
    is_btn = (btn_g.astype(int) - btn_b.astype(int) > 10)
    
    # 4. ต้องไม่มีปุ่ม Cancel สีเทาฝั่งซ้าย (ถ้ามีแสดงว่าเป็น Quit watching?)
    roi_cancel = img[440:530, 350:520]
    mask_cancel = (np.abs(roi_cancel[:, :, 0].astype(int) - roi_cancel[:, :, 1].astype(int)) < 15) & \
                  (np.abs(roi_cancel[:, :, 1].astype(int) - roi_cancel[:, :, 2].astype(int)) < 15) & \
                  (roi_cancel[:, :, 0] > 90) & (roi_cancel[:, :, 0] < 160)
    has_cancel = mask_cancel.sum() > 2000
    
    return bool(is_grey_card.sum() > 20000 and is_btn.sum() > 2000 and not has_cancel)

def check_inviting_player_popup(img):
    # ปุ่ม Confirm สีเขียวบนหน้าต่าง Inviting player (x: 550..720, y: 480..580)
    roi = img[480:580, 550:720]
    mask = (roi[:, :, 1] > 150) & (roi[:, :, 0] < 70) & (roi[:, :, 2] > 100)
    return mask.sum() > 2500

def generate_random_nickname():
    """bot + ชื่อสุ่ม (คำหรือตัวอักษร 2-3 ตัว) + ตัวเลขสุ่ม 4-6 ตัว"""
    words = [
        "run", "fast", "dash", "star", "joy", "hero", "pro", "sky",
        "jump", "neo", "max", "ice", "cool", "luck", "ace", "pop",
        "fly", "fox", "cat", "sun", "red", "gem", "win", "bee"
    ]
    if random.random() < 0.7:
        rand_name = random.choice(words)
    else:
        rand_name = "".join(random.choices(string.ascii_lowercase, k=random.randint(2, 3)))

    digits = "".join(random.choices(string.digits, k=random.randint(4, 6)))
    nick = f"bot{rand_name}{digits}"
    if len(nick) > 12:
        nick = nick[:12]
    return nick

def clear_all_lobby_popups(max_wait=35, desc="Lobby"):
    """วนลูปตรวจจับและปิด Popup ทุกชนิด (Congratulations, Welcome Rewards, Banners, News, Select a Mode) จนกว่า Lobby จะสะอาดจริง 100%"""
    print(f"  -> เริ่มเคลียร์ Popup ทั้งหมด ({desc}) ตรวจจออย่างรัดกุม...", flush=True)
    t_end = time.time() + max_wait
    while time.time() < t_end:
        img = device_capture_screen(DEVICE)
        if img is None:
            time.sleep(0.5)
            continue

        # 1. ตรวจสอบหน้าต่างข่าวสาร / แบนเนอร์ (X กลมสีเทา 1125, 72)
        if check_banner_or_news_popup(img):
            print("  ⚡ พบหน้าต่างข่าวสาร/ประกาศ -> กดปิด X (1125, 72)...", flush=True)
            tap(1125, 72, delay=1.2)
            continue

        # 2. ตรวจสอบหน้าต่าง Select a Mode (X สีม่วง 1215, 95)
        if check_select_mode_popup(img):
            print("  ⚡ พบหน้าต่าง Select a Mode -> กดปิด X (1215, 95)...", flush=True)
            tap(1215, 95, delay=1.2)
            continue

        # 3. ตรวจสอบปุ่ม Confirm สีเขียวกลางจอ (Congratulations / Daily Check-in / Welcome Rewards)
        roi_center = img[440:680, 480:710]
        mask_c = ((roi_center[:, :, 1] > 140) & (roi_center[:, :, 0] < 80) & (roi_center[:, :, 2] > 90)).astype(np.uint8)
        n_c, _, stats_c, centroids_c = cv2.connectedComponentsWithStats(mask_c)
        found_center = None
        for k in range(1, n_c):
            area = stats_c[k, cv2.CC_STAT_AREA]
            cx = int(centroids_c[k][0]) + 480
            cy = int(centroids_c[k][1]) + 440
            if area > 3000 and cx < 720:
                found_center = (cx, cy)
                break

        if found_center:
            print(f"  -> พบ Popup รางวัล/ยินดีต้อนรับ กลางจอ -> กด Confirm {found_center}...", flush=True)
            tap(found_center[0], found_center[1], delay=1.2)
            continue

        # 4. ตรวจสอบว่าถึงหน้า Lobby มีปุ่ม Play! สีเขียวขวาล่าง
        roi_play = img[580:710, 750:950]
        mask_play = ((roi_play[:, :, 1] > 150) & (roi_play[:, :, 0] < 70) & (roi_play[:, :, 2] > 90)).astype(np.uint8)
        if mask_play.sum() > 3000:
            # ตรวจสอบซ้ำอีกครั้งหลังรอ 1.5 วิ เพื่อยืนยันว่าไม่มี Popup ใดๆ เด้งตามมาอีก
            time.sleep(1.5)
            chk = device_capture_screen(DEVICE)
            if chk is not None:
                chk_news = check_banner_or_news_popup(chk)
                chk_mode = check_select_mode_popup(chk)
                chk_c = False
                c_chk_roi = chk[440:680, 480:710]
                c_chk_mask = ((c_chk_roi[:, :, 1] > 140) & (c_chk_roi[:, :, 0] < 80) & (c_chk_roi[:, :, 2] > 90)).astype(np.uint8)
                n_chk, _, s_chk, cnts_chk = cv2.connectedComponentsWithStats(c_chk_mask)
                for k in range(1, n_chk):
                    if s_chk[k, cv2.CC_STAT_AREA] > 3000 and (int(cnts_chk[k][0]) + 480 < 720):
                        chk_c = True
                        break
                if not chk_news and not chk_mode and not chk_c:
                    print("  ⚡ ยืนยันหน้า Lobby เรียบร้อย สะอาด 100%!", flush=True)
                    return True
        time.sleep(1.0)
    return False

# =========================================================================
# MAIN FAST FLOW
# =========================================================================

def run_fast_flow():
    print("\n" + "=" * 60)
    print("🚀 เริ่มรัน Fast Flow (Real-time Image Detection)")
    print("=" * 60)

    # ---------------------------------------------------------------------
    print("\n[STEP 0] ล้างข้อมูลล็อกอิน/แคช (เก็บแพตช์เกม) + ตรวจสิทธิ์ Root + เปิดเกม")
    # ---------------------------------------------------------------------
    adb('shell', 'am', 'force-stop', PACKAGE)
    time.sleep(0.5)
    try:
        from adb import ensure_adb_root
        ensure_adb_root(DEVICE)
    except Exception:
        pass

    try:
        adb('shell', 'chmod', '755', '/system/xbin/su', timeout=2)
        adb('shell', 'chmod', '755', '/system/bin/su', timeout=2)
    except Exception:
        pass

    rm_cmd = (f"rm -rf /data/data/{PACKAGE}/shared_prefs "
              f"/data/data/{PACKAGE}/databases "
              f"/data/data/{PACKAGE}/cache "
              f"/data/data/{PACKAGE}/code_cache "
              f"/data/data/{PACKAGE}/app_webview "
              f"/sdcard/Android/data/{PACKAGE}/cache")
    adb('shell', rm_cmd)
    adb('shell', 'su', '-c', f"'{rm_cmd}'")

    check_sp = adb('shell', f"ls -d /data/data/{PACKAGE}/shared_prefs 2>/dev/null")
    if check_sp and "shared_prefs" in (check_sp.stdout or ""):
        adb('shell', f"rm -rf /data/data/{PACKAGE}/shared_prefs/* /data/data/{PACKAGE}/databases/*")
        adb('shell', 'su', '-c', f"'rm -rf /data/data/{PACKAGE}/shared_prefs/* /data/data/{PACKAGE}/databases/*'")

    try:
        adb('shell', 'chmod', '000', '/system/xbin/su', timeout=2)
        adb('shell', 'chmod', '000', '/system/bin/su', timeout=2)
    except Exception:
        pass

    adb('shell', 'monkey', '-p', PACKAGE, '-c', 'android.intent.category.LAUNCHER', '1')
    cap("s0_launched")

    # ---------------------------------------------------------------------
    print("\n[STEP 1a] ตรวจจับหน้าต่าง Age Selection")
    # ---------------------------------------------------------------------
    ok, _ = wait_until(check_age_popup, timeout=25, desc="Age Popup")
    if ok:
        tap(770, 370, delay=0.4)  # เลื่อน slider ไปขวา
        tap(640, 406, delay=1.0)  # Confirm
        cap("s1a_age_confirmed")

    # ---------------------------------------------------------------------
    print("\n[STEP 1b] ตรวจจับหน้าต่าง Terms of Service")
    # ---------------------------------------------------------------------
    ok, _ = wait_until(check_tos_popup, timeout=12, desc="TOS Popup")
    if ok:
        tap(801, 443, delay=1.0)  # OK
        cap("s1b_tos_confirmed")

    # ---------------------------------------------------------------------
    print("\n[STEP 1c] ตรวจจับปุ่ม DevPlay Login บน Title Screen")
    # ---------------------------------------------------------------------
    ok, _ = wait_until(check_devplay_login_btn, timeout=15, desc="DevPlay Login Button")
    if ok:
        tap(520, 622, delay=1.2)
        cap("s1c_devplay_login_tapped")

    # ---------------------------------------------------------------------
    print("\n[STEP 1d] ตรวจจับปุ่ม Sign in with E-mail")
    # ---------------------------------------------------------------------
    ok, _ = wait_until(check_email_signin_btn, timeout=12, desc="Sign in with E-mail Button")
    if ok:
        tap(795, 391, delay=1.2)
        cap("s1d_email_signin_tapped")

    # ---------------------------------------------------------------------
    print("\n[STEP 2] ตรวจจับหน้าจอกรอก Email (รอโหลดเสร็จ 100%) แล้วกรอก Email สุ่ม")
    # ---------------------------------------------------------------------
    email_deadline = time.time() + 35
    email_ready = False
    retries = 0
    while time.time() < email_deadline:
        img = device_capture_screen(DEVICE)
        if check_email_input_page(img):
            email_ready = True
            print("  ⚡ เจอหน้าจอกรอก Email โหลดเสร็จสมบูรณ์!")
            break
        retries += 1
        if retries % 6 == 0:
            print("  -> หน้าเว็บยังไม่ขึ้น ลองแตะ Sign in with E-mail ซ้ำ...")
            tap(795, 391, delay=0.5)
        time.sleep(0.5)

    if email_ready:
        time.sleep(0.5)
        email = f"user_{int(time.time())}_{random.randint(1000,9999)}@gmail.com"
        print(f"  -> หน้าจอกรอกอีเมลพร้อมแล้ว! สุ่ม Email: {email}")
        tap(640, 210, delay=0.5)  # แตะกลางช่อง 'Type it in here'
        type_text(email)
        keyevent(66, delay=0.3)   # Enter
        keyevent(111, delay=0.3)  # Hide keyboard
        time.sleep(0.3)
        tap(638, 662, delay=1.2)  # Next button ด้านล่างของ modal
        cap("s2_email_submitted")

    # ---------------------------------------------------------------------
    print("\n[STEP 3] กรอก Password สุ่ม 2 ช่อง + ติ๊ก Agree")
    # ---------------------------------------------------------------------
    ok, _ = wait_until(check_password_input_page, timeout=12, desc="Password Input Page")
    password = f"kP9#mX2${random.randint(100,999)}!qR5@"
    # ช่อง 1
    tap(521, 207, delay=0.3)
    type_text(password)
    # ช่อง 2
    tap(521, 260, delay=0.3)
    type_text(password)
    keyevent(111, delay=0.3)  # Hide keyboard
    # ติ๊ก Agree
    tap(423, 328, delay=0.5)
    cap("s3_password_and_agree")

    # ---------------------------------------------------------------------
    print("\n[STEP 4] รอ Cloudflare เขียว + กด Register")
    # ---------------------------------------------------------------------
    cf_deadline = time.time() + 60
    taps = 0
    while time.time() < cf_deadline:
        img = device_capture_screen(DEVICE)
        if img is not None and check_cloudflare_green(img):
            print("  ⚡ Cloudflare = GREEN!", flush=True)
            cap("s4_cloudflare_green")
            break
        taps += 1
        if taps % 4 == 0:
            tap(434, 404, delay=0.2)  # แตะกระตุ้น
        time.sleep(0.8)

    # กด Register
    tap(638, 662, delay=1.0)
    cap("s4_registered")

    # ---------------------------------------------------------------------
    print("\n[STEP 5] ตรวจจับหน้าจอเพื่อข้ามวิดีโอ & คัตซีน (รอดูจอและเช็คจังหวะ ไม่กดเร็ว)")
    # ---------------------------------------------------------------------
    # 1. รอให้หน้าต่าง Webview ปิด และเกมโหลดเข้าสู่อนิเมชั่นอินโทรอย่างสมบูรณ์
    print("  -> รอหน้าเว็บ DevPlay ปิด และรอตัวเกมโหลดเข้าสู่อนิเมชั่นอินโทร (4 วินาที)...")
    time.sleep(4.0)

    video_deadline = time.time() + 60
    last_tap = 0
    while time.time() < video_deadline:
        img = device_capture_screen(DEVICE)
        if img is None:
            time.sleep(0.5)
            continue

        # 1. หน้าต่าง Quit watching? (ปุ่มเขียว Confirm อยู่ที่ 793, 456)
        if check_quit_watching_popup(img):
            print("  ⚡ เจอ Quit watching? -> กด Confirm (793, 456)...")
            tap(793, 456, delay=1.2)
            # ตรวจสอบจนกว่าหน้าต่าง Quit watching? จะปิดจริง (เว้นจังหวะ 1.2 วินาที)
            for _ in range(5):
                time.sleep(1.2)
                chk = device_capture_screen(DEVICE)
                if not check_quit_watching_popup(chk):
                    print("  ⚡ ปิดหน้าต่าง Quit watching? สำเร็จจริง 100%!")
                    break
                tap(793, 456, delay=1.0)
            cap("s5_quit_video_confirmed")
            continue

        # 2. หน้าต่าง 'Hi there! New to the game?' (ปุ่มเขียว Confirm อยู่ที่ 640, 464)
        if check_hi_there_popup(img):
            print("  ⚡ เจอ Hi there! -> กด Confirm (640, 464)...")
            tap(640, 464, delay=1.5)
            # ตรวจสอบจนกว่าหน้าต่าง Hi there! จะปิดจริง (เว้นจังหวะ 1.2 วินาที)
            for _ in range(5):
                time.sleep(1.2)
                chk = device_capture_screen(DEVICE)
                if not check_hi_there_popup(chk):
                    print("  ⚡ ปิดหน้าต่าง 'Hi there!' สำเร็จจริง 100%!")
                    break
                tap(640, 464, delay=1.0)
            cap("s5c_hi_there_confirmed")
            break

        # 3. ถึงห้อง Tutorial หรือเปิด Pause menu ขึ้นมาแล้ว
        if check_in_tutorial_room(img) or is_tutorial_pause_menu(img) or is_tutorial_confirm_quit_dialog(img):
            print("  ⚡ ถึงห้อง Tutorial เรียบร้อย!")
            break

        # 4. หากยังอยู่ในวิดีโอ -> รอดูจอก่อน แล้วแตะกลางจอทุก 2.5วิ เพื่อกระตุ้นหน้าต่าง Quit watching? (ไม่กดรัว)
        now = time.time()
        if now - last_tap > 2.5:
            print("  -> อยู่ในอนิเมชั่น: แตะกลางจอ 1 ครั้งเพื่อเรียกหน้าต่าง Quit watching?...")
            tap(640, 360, delay=0.3)
            last_tap = now

        time.sleep(1.5)

    # ---------------------------------------------------------------------
    print("\n[STEP 5d] ตรวจจับสถานะห้อง Tutorial ทุกๆ 1.2วิ -> ออกทันที พร้อมตรวจสอบว่าออกจริง")
    # ---------------------------------------------------------------------
    tut_deadline = time.time() + 45
    exited_tutorial = False
    last_pause_tap = 0
    while time.time() < tut_deadline:
        img = device_capture_screen(DEVICE)
        if img is None:
            time.sleep(0.5)
            continue

        # 0. จัดการหน้าต่างอนิเมชั่น/คัตซีนที่อาจหลงเหลือมา (Quit watching? หรือ Hi there!)
        if check_quit_watching_popup(img):
            print("  ⚡ ตรวจพบ Quit watching? -> กด Confirm (793, 456)...")
            tap(793, 456, delay=1.2)
            continue

        if check_hi_there_popup(img):
            print("  ⚡ ตรวจพบ Hi there! -> กด Confirm (640, 464)...")
            tap(640, 464, delay=1.2)
            continue

        # 1. ตรวจสอบสถานะความสำเร็จสูงสุด: ถึงหน้าต่างตั้งชื่อเล่น หรือถึง Lobby แล้ว
        if check_set_nickname_popup(img):
            print("  ⚡ ออกจากห้อง Tutorial สำเร็จ 100%! ถึงหน้าต่างตั้งชื่อเล่นแล้ว")
            exited_tutorial = True
            break

        # 2. สถานะ: หน้าต่างยืนยัน Confirm Quit ("Quit the tutorial?")
        # มีปุ่ม Quit สีฟ้าที่ (631, 378) และ Cancel สีเทาที่ (629, 525)
        if is_tutorial_confirm_quit_dialog(img):
            print("  ⚡ ตรวจพบ Confirm Quit Dialog -> แตะปุ่ม Quit (631, 378)...")
            tap(631, 378, delay=0.8)
            # ตรวจสอบจนกว่าหน้าต่างนี้จะปิดจริง (รอ 1 วิ เพื่อให้แอนิเมชันเสร็จสมบูรณ์)
            for _ in range(5):
                time.sleep(1.0)
                chk = device_capture_screen(DEVICE)
                if not is_tutorial_confirm_quit_dialog(chk):
                    print("  ⚡ ออกจาก Tutorial สำเร็จจริง!")
                    break
                tap(631, 378, delay=0.8)
            continue

        # 3. สถานะ: เมนู Pause Menu ("Continue" เขียวบน + "Quit" ฟ้าล่าง)
        # มีปุ่ม Quit สีฟ้าที่ (631, 423)
        if is_tutorial_pause_menu(img):
            print("  ⚡ ตรวจพบ Pause Menu -> แตะปุ่ม Quit (631, 423)...")
            tap(631, 423, delay=0.8)
            # ตรวจสอบจนกว่าจะเปิด Confirm Quit Dialog ขึ้นมาจริง
            for _ in range(5):
                time.sleep(1.0)
                chk = device_capture_screen(DEVICE)
                if is_tutorial_confirm_quit_dialog(chk) or check_set_nickname_popup(chk):
                    print("  ⚡ เปิดหน้าต่าง Confirm Quit สำเร็จจริง!")
                    break
                tap(631, 423, delay=0.8)
            continue

        # 4. สถานะ: อยู่ในห้องวิ่ง กำลังเล่น Tutorial
        # เคลียร์กล่องข้อความ "These Jellies" แล้วแตะ Pause ที่มุมขวาบน (1198, 38)
        now = time.time()
        if now - last_pause_tap > 1.5:
            # แตะจอเพื่อเคลียร์กล่องข้อความสอนเล่น
            tap(640, 360, delay=0.3)
            # แตะปุ่ม Pause || ขวาบน (1198, 38)
            tap(1198, 38, delay=0.5)
            last_pause_tap = now
            cap("s5d_tutorial_pause_attempt")

        time.sleep(1.2)

    if not exited_tutorial:
        print("  ❌ ออกจากห้อง Tutorial ไม่สำเร็จ! หยุดทันที ไม่ทำขั้นตอนถัดไปเด็ดขาด")
        return False

    # ---------------------------------------------------------------------
    print("\n[STEP 6] ตั้งชื่อเล่นสุ่ม 'bot' + ชื่อสุ่ม + ตัวเลข 4-6 หลัก")
    # ---------------------------------------------------------------------
    ok, _ = wait_until(check_set_nickname_popup, timeout=15, desc="Set Nickname Popup")
    nick = generate_random_nickname()
    print(f"  -> สุ่มชื่อ: {nick}")
    tap(638, 385, delay=0.8)  # ช่องใส่ชื่อ
    for _ in range(15):
        keyevent(67, delay=0.04)
    type_text(nick)
    time.sleep(0.5)
    keyevent(66, delay=0.3)
    keyevent(111, delay=0.5)
    time.sleep(1.0)
    print("  -> แตะปุ่ม Confirm (639, 487) ตั้งชื่อ...")
    tap(639, 487, delay=1.2)
    for _ in range(6):
        time.sleep(1.0)
        chk = device_capture_screen(DEVICE)
        if not check_set_nickname_popup(chk):
            print("  ⚡ ตั้งชื่อเล่นสำเร็จ หน้าต่างปิดเรียบร้อย 100%!")
            break
        tap(639, 487, delay=0.8)
    cap("s6_nickname_confirmed")

    # ---------------------------------------------------------------------
    print("\n[STEP 6b] เคลียร์ Popup รางวัลและข่าวสารทั้งหมดจนถึง Lobby")
    # ---------------------------------------------------------------------
    lobby_clean = clear_all_lobby_popups(max_wait=35, desc="Step 6b เคลียร์ก่อนเปิด OneLink")
    if lobby_clean:
        cap("s6b_lobby_clean")
    else:
        print("  ⚠️ เคลียร์ Popup ครบเวลา (Timeout) -> ดำเนินการขั้นตอนถัดไปต่อ")

    # ---------------------------------------------------------------------
    print("\n[STEP 7] เปิด OneLink ใน Browser -> รับเพื่อน")
    # ---------------------------------------------------------------------
    adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', INVITE_URL,
        '-n', 'com.android.chromium/org.chromium.chrome.browser.ChromeTabbedActivity')
    time.sleep(1.5)
    adb('shell', 'am', 'start', '-n', f'{PACKAGE}/com.devsisters.CookieRunForKakao.OvenbreakX')

    # ตรวจจับหน้าต่าง 'Inviting player' (ลด timeout เหลือ 8s)
    ok, _ = wait_until(check_inviting_player_popup, timeout=8, desc="Inviting Player Popup")
    if ok:
        print("  ⚡ พบหน้าต่าง Inviting Player -> กด Confirm (639, 537)")
        tap(639, 537, delay=1.2)  # Confirm ตอบรับ
        cap("s7_invite_confirmed")
    else:
        print("  ⚠️ ไม่พบหน้าต่าง Inviting Player (อาจตอบรับออโต้แล้ว)")

    # เคลียร์ Popup Welcome Rewards (Double EXP, Coins, Dough, Tickets, Keys) ทั้งหมดที่เด้งตามมา
    clear_all_lobby_popups(max_wait=20, desc="Step 7 เคลียร์ Welcome Rewards หลังรับเพื่อน")

    # ดีเลย์ 1 วิ แล้วกดเช็คเพื่อนทันทีตามที่ผู้ใช้สั่ง
    print("  -> ดีเลย์ 1 วิ แล้วแตะไอคอน Friends (800, 335) เพื่อเช็ค/ซิงก์เพื่อน...")
    time.sleep(1.0)
    tap(800, 335, delay=1.0)

    # รอจนกว่าหน้าต่าง Friends จะเปิดขึ้นมาจริง (ตรวจปุ่ม X 1009, 69)
    print("  [รอ] หน้าต่าง Friends เปิดขึ้นมาจริง...")
    for _ in range(12):
        img_f = device_capture_screen(DEVICE)
        if img_f is not None:
            roi_x = img_f[50:90, 990:1030]
            if float(roi_x.mean()) > 100:
                print("  ⚡ หน้าต่าง Friends เปิดขึ้นมาเรียบร้อยแล้ว!")
                cap("s7_friends_opened")
                break
        time.sleep(0.5)

    time.sleep(1.5)  # รอให้รายชื่อเพื่อนแสดงผลและซิงก์ข้อมูลกับเซิร์ฟเวอร์

    # ปิดหน้าต่าง Friends (1009, 69)
    print("  -> กดปิดหน้าต่าง Friends (1009, 69)...")
    tap(1009, 69, delay=1.0)

    # รอจนกว่าหน้าต่าง Friends จะปิดสนิทจริง และกลับสู่หน้า Lobby
    print("  [รอ] หน้าต่าง Friends ปิดสนิทและกลับสู่หน้า Lobby...")
    for _ in range(10):
        img_l = device_capture_screen(DEVICE)
        if img_l is not None:
            roi_x = img_l[50:90, 990:1030]
            if float(roi_x.mean()) < 80:
                print("  ⚡ หน้าต่าง Friends ปิดเรียบร้อย กลับสู่หน้า Lobby จริง!")
                cap("s7_friends_closed")
                break
        time.sleep(0.5)
    time.sleep(1.0)

    # ---------------------------------------------------------------------
    print("\n[STEP 8] ส่งหัวใจให้เพื่อนอันดับ 1 (รอตรวจจับปุ่มจริง ไม่กดมั่ว)")
    # ---------------------------------------------------------------------
    heart_ready = False
    print("  [รอ] ตรวจสอบปุ่มส่งหัวใจ Rank 1 บนหน้า Lobby...")
    for _ in range(15):
        img = device_capture_screen(DEVICE)
        if img is None:
            time.sleep(0.5)
            continue

        # ถ้ามี popup อะไรค้างอยู่ ให้เคลียร์ก่อน
        roi_c = img[440:680, 480:710]
        mask_c = ((roi_c[:, :, 1] > 140) & (roi_c[:, :, 0] < 80) & (roi_c[:, :, 2] > 90)).astype(np.uint8)
        if cv2.countNonZero(mask_c) > 3000:
            tap(638, 563, delay=1.0)
            continue

        # ตรวจสอบปุ่ม Rank 1: บริเวณ x: 610..700, y: 280..360
        roi_rank1 = img[280:360, 610:700]
        hsv_r1 = cv2.cvtColor(roi_rank1, cv2.COLOR_BGR2HSV)
        mask_green = cv2.inRange(hsv_r1, (35, 100, 100), (85, 255, 255))
        mask_red = ((hsv_r1[:, :, 0] < 10) | (hsv_r1[:, :, 0] > 170)) & (hsv_r1[:, :, 1] > 150) & (hsv_r1[:, :, 2] > 150)

        if mask_green.sum() > 2000 and mask_red.sum() > 50:
            print("  ⚡ ตรวจพบปุ่มส่งหัวใจ Rank 1 (Active) บนหน้า Lobby!")
            heart_ready = True
            break
        elif mask_green.sum() > 2000 and mask_red.sum() <= 50:
            print("  ✅ ตรวจพบเครื่องหมายถูกสีเขียวที่ Rank 1 (หัวใจถูกส่งแล้ว)!")
            heart_ready = "already_sent"
            break

        time.sleep(0.8)

    if heart_ready == True:
        print("  -> แตะปุ่มส่งหัวใจ Rank 1 (655, 320)...")
        tap(655, 320, delay=1.0)

        # รอหน้าต่าง 'Send free Life?' ปรากฏจริง
        print("  [รอ] หน้าต่าง 'Send free Life?'...")
        for _ in range(10):
            img_c = device_capture_screen(DEVICE)
            if img_c is not None:
                roi_cf = img_c[420:490, 720:860]
                hsv_cf = cv2.cvtColor(roi_cf, cv2.COLOR_BGR2HSV)
                mask_cf = cv2.inRange(hsv_cf, (35, 100, 100), (85, 255, 255))
                if mask_cf.sum() > 2000:
                    print("  ⚡ พบหน้าต่าง 'Send free Life?' -> กด Confirm (793, 456)")
                    tap(793, 456, delay=1.2)
                    break
            time.sleep(0.4)

        # รอหน้าต่าง 'Message sent!' ปรากฏจริง
        print("  [รอ] หน้าต่าง 'Message sent!'...")
        for _ in range(10):
            img_m = device_capture_screen(DEVICE)
            if img_m is not None:
                roi_msg = img_m[420:490, 560:720]
                hsv_msg = cv2.cvtColor(roi_msg, cv2.COLOR_BGR2HSV)
                mask_msg = cv2.inRange(hsv_msg, (35, 100, 100), (85, 255, 255))
                if mask_msg.sum() > 2000:
                    print("  ⚡ พบหน้าต่าง 'Message sent!' -> กด Confirm (640, 456)")
                    tap(640, 456, delay=1.2)
                    break
            time.sleep(0.4)

        time.sleep(1.0)
        cap("s8_heart_sent_verified")
        print("  🎉 ยืนยัน: ส่งหัวใจให้เพื่อนอันดับ 1 สำเร็จเสร็จสิ้น 100%!")
    elif heart_ready == "already_sent":
        cap("s8_heart_already_sent")
        print("  🎉 ยืนยัน: หัวใจอันดับ 1 อยู่ในสถานะส่งเรียบร้อยแล้ว (เครื่องหมายถูกสีเขียว)!")
    else:
        print("  ⚠️ ไม่พบบุ่มส่งหัวใจที่ Rank 1 ภายในเวลา")
    print("\n" + "=" * 60)
    print("🎉 FAST FLOW COMPLETE! ทำงานเสร็จสมบูรณ์รวดเร็ว 100%")
    print(f"Screenshots: {OUT_DIR}")
    print("=" * 60)

if __name__ == '__main__':
    run_fast_flow()
