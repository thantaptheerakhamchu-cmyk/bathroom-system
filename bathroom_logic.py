import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

app = Flask(__name__)
CORS(app) 

# ดึงรหัสกุญแจลับจากไฟล์ .env (ปลอดภัยกว่าเดิม)
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
YOUR_USER_ID = os.getenv('YOUR_USER_ID')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

# --- ส่วนที่ 1: หน่วยความจำชั่วคราวจำสถานะห้องน้ำ ---
rooms_status = {
    "1": {"status": "สะอาด", "color": "green"},
    "2": {"status": "สะอาด", "color": "green"},
    "3": {"status": "สะอาด", "color": "green"}
}

# --- ส่วนที่ 2: ช่องทางดึงสถานะไปแสดงผล ---
@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(rooms_status)

@app.route('/report', methods=['POST'])
def handle_report():
    try:
        data = request.json
        room = str(data.get('room'))
        issue = data.get('issue')
        note = data.get('note', '-')

        # ถ้าแจ้งเรื่องความสะอาด ให้เปลี่ยนสถานะเป็น 'ไม่สะอาด'
        if issue == "ความสะอาด/พื้นเปียก":
            rooms_status[room] = {"status": "ไม่สะอาด", "color": "red"}

        # ออกแบบข้อความแจ้งเตือนเข้า LINE
        message_text = (
            f"📢 [แจ้งซ่อม/ทำความสะอาด]\n"
            f"📍 สถานที่: ห้องน้ำที่ {room}\n"
            f"⚠️ ปัญหา: {issue}\n"
            f"📝 รายละเอียด: {note}\n"
            f"⏰ เวลา: 2026-01-22 12:04" # อัปเดตเวลาปัจจุบัน
        )

        line_bot_api.push_message(YOUR_USER_ID, TextSendMessage(text=message_text))
        
        return jsonify({"status": "success", "message": "ส่งข้อมูลและอัปเดตสถานะสำเร็จ!"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ส่วนที่ 3: ช่องทางสำหรับ Admin เพื่อล้างสถานะ ---
@app.route('/reset_status', methods=['POST'])
def reset_status():
    try:
        data = request.json
        room = str(data.get('room'))
        rooms_status[room] = {"status": "สะอาด", "color": "green"}
        return jsonify({"status": "success", "message": f"ห้องที่ {room} กลับมาสะอาดแล้ว!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # เปลี่ยนเป็น 0.0.0.0 เพื่อให้เครื่องอื่นในวงแลนเข้าถึงได้
    app.run(debug=True, host='0.0.0.0', port=5000)