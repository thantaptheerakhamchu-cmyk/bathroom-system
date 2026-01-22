from flask import Flask, request, jsonify
from flask_cors import CORS
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)
CORS(app) 

# รหัสกุญแจ LINE ของคุณ
CHANNEL_SECRET = 'c7e12914aace4e7560247ba96453d752'
LINE_ACCESS_TOKEN = '4osdkFfAQlp1ejc0f2FP7bUWPWJK87ilIuTK1CSgWzbMGZzM2050Lm4aEfN+YVjCjyu24VBP/qzzmb1FT/EMxsok+jHdo14Qc6SGUCjMxouWGE9Ql53LtSLDj8EX5y/5vcZ+dwEGNqp325quq+W67wdB04t89/1O/w1cDnyilFU='
YOUR_USER_ID = 'Ue245f5522acbdea06115091b2958ab69'

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

# --- ส่วนที่ 1: สร้าง "หน่วยความจำชั่วคราว" เพื่อจำสถานะห้องน้ำ ---
# เริ่มต้นให้ทุกห้อง (1, 2, 3) เป็น 'สะอาด' (green)
rooms_status = {
    "1": {"status": "สะอาด", "color": "green"},
    "2": {"status": "สะอาด", "color": "green"},
    "3": {"status": "สะอาด", "color": "green"}
}

# --- ส่วนที่ 2: ช่องทางให้หน้าเว็บ (ทั้ง Index และ Admin) มาดึงสถานะไปแสดงผล ---
@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(rooms_status)

@app.route('/report', methods=['POST'])
def handle_report():
    try:
        data = request.json
        room = str(data.get('room')) # ดึงเลขห้อง
        issue = data.get('issue')
        note = data.get('note', '-')

        # --- ส่วนที่เพิ่ม: ถ้ามีการแจ้งเรื่องความสะอาด ให้เปลี่ยนสถานะห้องนั้นเป็น 'ไม่สะอาด' ---
        if issue == "ความสะอาด/พื้นเปียก":
            rooms_status[room] = {"status": "ไม่สะอาด", "color": "red"}

        # ส่งข้อความเข้า LINE เหมือนเดิม
        message_text = (
            f"📢 [แจ้งซ่อม/ทำความสะอาด]\n"
            f"📍 สถานที่: ห้องน้ำที่ {room}\n"
            f"⚠️ ปัญหา: {issue}\n"
            f"📝 รายละเอียด: {note}"
        )

        line_bot_api.push_message(YOUR_USER_ID, TextSendMessage(text=message_text))
        
        return jsonify({"status": "success", "message": "ส่งข้อมูลเข้า LINE และอัปเดตสถานะแล้ว!"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ส่วนที่ 3: ช่องทางสำหรับหน้า Admin (แม่บ้าน) เพื่อกดล้างสถานะกลับเป็นปกติ ---
@app.route('/reset_status', methods=['POST'])
def reset_status():
    try:
        data = request.json
        room = str(data.get('room'))
        
        # เปลี่ยนสถานะกลับเป็น 'สะอาด' (green)
        rooms_status[room] = {"status": "สะอาด", "color": "green"}
        
        return jsonify({"status": "success", "message": f"ห้องที่ {room} กลับมาสะอาดแล้ว!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)