import os
import time
import sqlite3 # [เพิ่ม] สำหรับจัดการฐานข้อมูล
from flask import Flask, request, jsonify
from flask_cors import CORS
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv
from datetime import datetime

# โหลดค่าจากไฟล์ .env
load_dotenv()

app = Flask(__name__)
CORS(app) 

# ดึงรหัสกุญแจลับจากไฟล์ .env
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
YOUR_USER_ID = os.getenv('YOUR_USER_ID')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

# --- ส่วนที่ 1: การจัดการ Database (SQLite) ---
DB_NAME = "bathroom.db"

def init_db():
    """ฟังก์ชันสร้างไฟล์ฐานข้อมูลและตารางเริ่มต้น"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # สร้างตารางชื่อ rooms
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id TEXT PRIMARY KEY,
                status TEXT,
                color TEXT
            )
        ''')
        # ตรวจสอบว่ามีข้อมูลหรือยัง ถ้าไม่มีให้เพิ่มห้อง 1-5 เข้าไป
        cursor.execute('SELECT count(*) FROM rooms')
        if cursor.fetchone()[0] == 0:
            initial_data = [
                ('1', 'สะอาด', 'green'),
                ('2', 'สะอาด', 'green'),
                ('3', 'สะอาด', 'green'),
                ('4', 'สะอาด', 'green'),
                ('5', 'สะอาด', 'green')
            ]
            cursor.executemany('INSERT INTO rooms VALUES (?,?,?)', initial_data)
            conn.commit()
            print("--- สร้าง Database 'bathroom.db' และข้อมูลเริ่มต้นสำเร็จ! ---")

# สั่งให้ฐานข้อมูลเริ่มทำงานทันที
init_db()

def get_rooms_from_db():
    """ฟังก์ชันดึงข้อมูลจาก DB มาแปลงเป็น Dictionary เพื่อส่งให้หน้าเว็บ"""
    rooms_data = {}
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms")
        rows = cursor.fetchall()
        for row in rows:
            rooms_data[row['room_id']] = {
                "status": row['status'],
                "color": row['color']
            }
    return rooms_data

# --- ส่วนที่ 2: ระบบกันสแปม (Cooldown) ---
last_report_times = {} 
COOLDOWN_SECONDS = 60 

# --- ส่วนที่ 3: ช่องทางดึงสถานะไปแสดงผล ---
@app.route('/get_status', methods=['GET'])
def get_status():
    # ดึงข้อมูลล่าสุดจาก SQLite ส่งกลับไปที่หน้าเว็บ
    return jsonify(get_rooms_from_db())

@app.route('/report', methods=['POST'])
def handle_report():
    try:
        # [ด่านที่ 1] เช็กสแปม
        user_ip = request.remote_addr 
        current_time = time.time() 

        if user_ip in last_report_times:
            elapsed_time = current_time - last_report_times[user_ip]
            if elapsed_time < COOLDOWN_SECONDS:
                remaining = int(COOLDOWN_SECONDS - elapsed_time)
                return jsonify({
                    "status": "error", 
                    "message": f"ใจเย็นๆ ครับ! กรุณารออีก {remaining} วินาทีแล้วค่อยแจ้งใหม่"
                }), 429

        last_report_times[user_ip] = current_time

        # [ด่านที่ 2] จัดการข้อมูล
        data = request.json
        room = str(data.get('room'))
        issue = data.get('issue')
        note = data.get('note', '-')

        # อัปเดตสถานะลงใน SQLite (ถ้าเป็นเรื่องความสะอาด)
        if issue == "ความสะอาด/พื้นเปียก":
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE rooms SET status=?, color=? WHERE room_id=?", 
                             ('ไม่สะอาด', 'red', room))
                conn.commit()

        # [ด่านที่ 3] ส่งแจ้งเตือนเข้า LINE
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
        message_text = (
            f"📢 [แจ้งซ่อม/ทำความสะอาด]\n"
            f"📍 สถานที่: ห้องน้ำที่ {room}\n"
            f"⚠️ ปัญหา: {issue}\n"
            f"📝 รายละเอียด: {note}\n"
            f"⏰ เวลา: {current_datetime}" 
        )

        line_bot_api.push_message(YOUR_USER_ID, TextSendMessage(text=message_text))
        
        return jsonify({"status": "success", "message": "ส่งข้อมูลและอัปเดตลงฐานข้อมูลสำเร็จ!"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ส่วนที่ 4: ช่องทางสำหรับ Admin เพื่อล้างสถานะ ---
@app.route('/reset_status', methods=['POST'])
def reset_status():
    try:
        data = request.json
        room = str(data.get('room'))
        
        # รีเซ็ตสถานะใน SQLite ให้กลับเป็นสะอาด (สีเขียว)
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE rooms SET status=?, color=? WHERE room_id=?", 
                         ('สะอาด', 'green', room))
            conn.commit()
            
        return jsonify({"status": "success", "message": f"ห้องที่ {room} กลับมาสะอาดแล้ว!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)