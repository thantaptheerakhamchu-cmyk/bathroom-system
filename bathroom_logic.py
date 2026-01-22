from flask import Flask, request, jsonify
from flask_cors import CORS
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)
CORS(app) # อนุญาตให้หน้าเว็บส่งข้อมูลข้ามมาหา Python ได้

CHANNEL_SECRET = 'c7e12914aace4e7560247ba96453d752'
LINE_ACCESS_TOKEN = '4osdkFfAQlp1ejc0f2FP7bUWPWJK87ilIuTK1CSgWzbMGZzM2050Lm4aEfN+YVjCjyu24VBP/qzzmb1FT/EMxsok+jHdo14Qc6SGUCjMxouWGE9Ql53LtSLDj8EX5y/5vcZ+dwEGNqp325quq+W67wdB04t89/1O/w1cDnyilFU='
YOUR_USER_ID = 'Ue245f5522acbdea06115091b2958ab69'

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

@app.route('/report', methods=['POST'])
def handle_report():
    try:
        data = request.json
        room = data.get('room')
        issue = data.get('issue')
        note = data.get('note', '-')

        # ออกแบบข้อความที่จะส่งเข้า LINE
        # ในฐานะเจ้าของร้าน "ตัวแห้งไอที" เราต้องทำข้อความให้ดูเป็นมืออาชีพครับ
        message_text = (
            f"📢 [แจ้งซ่อม/ทำความสะอาด]\n"
            f"📍 สถานที่: ห้องน้ำที่ {room}\n"
            f"⚠️ ปัญหา: {issue}\n"
            f"📝 รายละเอียด: {note}\n"
            f"⏰ เวลา: 2026-01-15 11:39" # เวลาปัจจุบันที่คุณกำลังทดสอบ
        )

        # คำสั่งส่งข้อความเข้า LINE
        line_bot_api.push_message(YOUR_USER_ID, TextSendMessage(text=message_text))
        
        return jsonify({"status": "success", "message": "ส่งข้อมูลเข้า LINE สำเร็จ!"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # รันเซิร์ฟเวอร์ที่พอร์ต 5000
    app.run(debug=True, port=5000)