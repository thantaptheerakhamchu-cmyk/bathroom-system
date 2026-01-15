# ระบบจำลองการจัดการสถานะห้องน้ำ (Bathroom Management System)
def check_bathroom_status(room_number, is_clean, has_equipment):
    print(f"--- รายงานสถานะห้องน้ำที่ {room_number} ---")
    
    if not is_clean:
        print("⚠️ สถานะ: สกปรก! กำลังส่งข้อมูลไปยัง LINE Messaging API...")
    else:
        print("✅ สถานะ: สะอาดเรียบร้อย")

    if not has_equipment:
        print("❌ คำเตือน: อุปกรณ์ (ถัง/ขัน) ไม่ครบ")
    else:
        print("✅ อุปกรณ์: ครบถ้วน")

# จำลองข้อมูลจากหน้าเว็บ (ที่พนักงานกดส่งมา)
# ห้องที่ 2: สกปรก และ ไม่มีถังน้ำ
check_bathroom_status(room_number=2, is_clean=False, has_equipment=False)