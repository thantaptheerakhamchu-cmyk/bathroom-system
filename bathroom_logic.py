import os
import time
import sqlite3
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id TEXT PRIMARY KEY,
                status TEXT,
                color TEXT
            )
        ''')
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

init_db()

def get_rooms_from_db():
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

# --- ส่วนที่ 3: API สำหรับดึงข้อมูลและรายงาน ---

@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(get_rooms_from_db())

@app.route('/report', methods=['POST'])
def handle_report():
    try:
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

        data = request.json
        room = str(data.get('room'))
        issue = data.get('issue')
        note = data.get('note', '-')

        if issue == "ความสะอาด/พื้นเปียก":
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE rooms SET status=?, color=? WHERE room_id=?", 
                             ('ไม่สะอาด', 'red', room))
                conn.commit()

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

# --- ส่วนที่ 4: ฟังก์ชัน CRUD เพิ่มเติม (Create & Update) ---

@app.route('/reset_status', methods=['POST'])
def reset_status():
    """[U - Update] รีเซ็ตสถานะห้องกลับเป็นปกติ"""
    try:
        data = request.json
        room = str(data.get('room'))
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE rooms SET status=?, color=? WHERE room_id=?", 
                         ('สะอาด', 'green', room))
            conn.commit()
            
        return jsonify({"status": "success", "message": f"ห้องที่ {room} กลับมาสะอาดแล้ว!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/add_room', methods=['POST'])
def add_room():
    """[C - Create] เพิ่มห้องน้ำใหม่เข้าสู่ระบบ"""
    try:
        data = request.json
        room_id = str(data.get('room_id'))
        
        if not room_id:
            return jsonify({"status": "error", "message": "กรุณาระบุเลขห้อง"}), 400

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # ตรวจสอบก่อนว่ามีห้องนี้อยู่แล้วหรือไม่
            cursor.execute("SELECT room_id FROM rooms WHERE room_id=?", (room_id,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": f"ห้องที่ {room_id} มีอยู่ในระบบแล้ว"}), 400
            
            # เพิ่มห้องใหม่สถานะเริ่มต้นคือสะอาด (สีเขียว)
            cursor.execute("INSERT INTO rooms (room_id, status, color) VALUES (?, 'สะอาด', 'green')", (room_id,))
            conn.commit()
            
        return jsonify({"status": "success", "message": f"เพิ่มห้องที่ {room_id} เข้าสู่ระบบสำเร็จ!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_room', methods=['POST'])
def delete_room():
    """[D - Delete] ลบห้องน้ำออกจากระบบ"""
    try:
        data = request.json
        room_id = str(data.get('room_id'))
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # เช็กก่อนว่ามีห้องนี้ไหม
            cursor.execute("SELECT room_id FROM rooms WHERE room_id=?", (room_id,))
            if not cursor.fetchone():
                return jsonify({"status": "error", "message": f"ไม่พบห้องที่ {room_id} ในระบบ"}), 404
            
            # สั่งลบแถว (Row) นั้นทิ้ง
            cursor.execute("DELETE FROM rooms WHERE room_id=?", (room_id,))
            conn.commit()
            
        return jsonify({"status": "success", "message": f"ลบห้องที่ {room_id} ออกจากระบบเรียบร้อย!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)