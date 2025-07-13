# LuckyDraw System v1.6 - Phase 5 FINAL Complete! 🎯

ระบบจับรางวัลที่รองรับทั้งโหมดคลาสสิกและแลกเปลี่ยนของขวัญ พร้อม Admin Dashboard แบบ Interactive พร้อม Sound Effects, Confetti Animation, Customization และ Safeguards ครบครัน

## การติดตั้ง

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt

# สร้างข้อมูลตัวอย่าง (ครั้งแรก)
python create_sample_data.py

# รันแอปพลิเคชัน
python app.py
```

## การใช้งานครั้งแรก

1. รันคำสั่งติดตั้ง
2. ไปที่ http://localhost:5001 
3. เข้า Dashboard อีเวนต์ตัวอย่าง:
   - Classic Mode: http://localhost:5001/event/1
   - Exchange Mode: http://localhost:5001/event/2

## โครงสร้างโปรเจกต์

```
04_LuckyDraw/
├── app.py                        # Flask application หลัก
├── models.py                     # Database models
├── create_sample_data.py         # สร้างข้อมูลตัวอย่าง
├── requirements.txt              # Python dependencies
├── README.md                     # เอกสารนี้
├── static/
│   ├── audio/
│   │   └── README.md             # คู่มือไฟล์เสียง
│   └── js/
│       └── dashboard.js          # JavaScript สำหรับ Dashboard
├── templates/
│   └── event_dashboard.html      # หน้า Dashboard อีเวนต์
└── luckydraw.db                  # SQLite database (สร้างอัตโนมัติ)
```

## API Endpoints

### GET /
หน้าแรกของระบบ

### GET /event/<event_id>
หน้า Dashboard ของอีเวนต์

### POST /api/event/<event_id>/draw
จับรางวัล

### GET /api/event/<event_id>/state
ดูสถานะปัจจุบันของอีเวนต์

### POST /api/event/<event_id>/add_participant
เพิ่มผู้เข้าร่วม

### POST /api/event/<event_id>/add_prize
เพิ่มรางวัล (เฉพาะโหมดคลาสสิก)

### POST /api/event/<event_id>/reset
รีเซ็ตอีเวนต์ (ลบประวัติและรีเซ็ตรางวัล)

### POST /api/event/<event_id>/settings
อัปเดตการตั้งค่าอีเวนต์ (ธีม, เสียง, อนิเมชัน)

### POST /api/event/<event_id>/toggle_test_mode
เปิด/ปิดโหมดทดสอบ

### POST /api/event/<event_id>/undo_draw
ยกเลิกการจับรางวัลครั้งล่าสุด

**Response สำหรับโหมดคลาสสิก:**
```json
{
  "success": true,
  "winner_name": "ชื่อผู้โชคดี",
  "prize_name": "ชื่อรางวัล",
  "draw_type": "classic"
}
```

**Response สำหรับโหมดแลกเปลี่ยน:**
```json
{
  "success": true,
  "giver_name": "ชื่อผู้ให้",
  "receiver_name": "ชื่อผู้รับ",
  "draw_type": "exchange"
}
```

## Database Schema

### Events
- ข้อมูลอีเวนต์และการตั้งค่าต่างๆ
- รองรับโหมดทดสอบ (`is_test_mode`)

### Participants  
- รายชื่อผู้เข้าร่วมในแต่ละอีเวนต์

### Prizes
- รางวัลและจำนวนคงเหลือ (สำหรับโหมดคลาสสิก)

### History
- ประวัติการจับรางวัล รองรับทั้ง 2 โหมด

## Core Logic

### โหมดคลาสสิก (Classic)
1. สุ่มเลือกผู้เข้าร่วมที่ยังไม่เคยได้รางวัล
2. สุ่มเลือกรางวัลที่ยังมีจำนวนคงเหลือ
3. ลดจำนวนรางวัลและบันทึกประวัติ

### โหมดแลกเปลี่ยน (Exchange)
1. กำหนดผู้ให้ (ครั้งแรก = ผู้เข้าร่วมคนแรก, ครั้งถัดไป = ผู้รับจากครั้งก่อน)
2. สุ่มเลือกผู้รับที่ยังไม่เคยได้รับ
3. บันทึกประวัติผู้ให้และผู้รับ

## ✅ Features ที่เสร็จแล้ว

### Phase 1: MVP - Core Logic
- ✅ Database Schema สมบูรณ์
- ✅ Core Logic ทั้ง 2 โหมด (Classic/Exchange)
- ✅ REST API endpoints

### Phase 2: Admin Dashboard & Interactivity  
- ✅ UI Dashboard สวยงามด้วย Tailwind CSS
- ✅ เพิ่มผู้เข้าร่วม/รางวัลผ่านหน้าเว็บ
- ✅ ปุ่มจับรางวัลแบบ Interactive
- ✅ แสดงผลแบบ Real-time
- ✅ Winner Announcement Modal พร้อม Confetti
- ✅ แสดงสถานะโหมดทดสอบ

### Phase 3: Transparency & Polish
- ✅ Sound Effects (Drum Roll + Tada)
- ✅ Canvas Confetti Animation แบบ Professional
- ✅ Visual Randomization Animation ระหว่างสุ่ม
- ✅ Reset Event Functionality
- ✅ Enhanced User Experience พร้อมเอฟเฟกต์พิเศษ

### Phase 4: Customization & Theming
- ✅ Settings Modal ครบครันสำหรับ Classic Mode
- ✅ ปรับความหน่วงเวลาในการสุ่ม (1-10 วินาที)
- ✅ เปลี่ยนข้อความบนปุ่มจับรางวัล
- ✅ เลือกเพลงประกอบ (4 ตัวเลือก)
- ✅ เลือกอนิเมชันการสุ่ม (4 รูปแบบ)
- ✅ เลือกอนิเมชันผู้ชนะ (Confetti, Fireworks, Balloons, Sparkles)
- ✅ ใส่รูปพื้นหลังและโลโก้ผ่าน URL
- ✅ Real-time Configuration Apply

### Phase 5: Safeguards & Testing
- ✅ Test Mode Toggle Switch พร้อม Banner แสดงสถานะ
- ✅ Draw API รองรับโหมดทดสอบ (ไม่บันทึกลงฐานข้อมูล)
- ✅ Undo Last Draw พร้อม Confirmation Dialog
- ✅ Auto-restore Prize Quantities และ Participant Status
- ✅ Enhanced Winner Announcement แสดงสถานะโหมดทดสอบ
- ✅ Complete Safeguard System สำหรับการใช้งานจริง

## 🎵 การใช้งาน Sound Effects

1. หาไฟล์เสียงจาก Freesound.org หรือ YouTube Audio Library
2. ใส่ไฟล์ใน `/static/audio/`:
   - `drumroll.mp3` - เสียงกลองระหว่างสุ่ม
   - `tada.mp3` - เสียงฉลองเมื่อออกผล
3. เบราว์เซอร์ต้องอนุญาตเล่นเสียงอัตโนมัติ

## ⚙️ การใช้งาน Customization

### การตั้งค่าผ่าน Settings Modal:
1. คลิกปุ่ม **"⚙️ ตั้งค่า"** ที่มุมขวาบนของ Dashboard
2. ปรับการตั้งค่าตามต้องการ:
   - **ความหน่วงเวลา**: 1-10 วินาที
   - **ข้อความปุ่ม**: เปลี่ยนจาก "จับรางวัล" เป็นอย่างอื่น
   - **เพลงและอนิเมชัน**: เลือกรูปแบบที่ชอบ
   - **รูปภาพ**: ใส่ URL สำหรับพื้นหลังและโลโก้
3. คลิก **"บันทึกการตั้งค่า"**
4. การตั้งค่าจะมีผลทันที!

### Animation Options:
- **การสุ่ม**: ชื่อวิ่งผ่าน, วงล้อหมุน, ไอคอนกระเด้ง, ฝนตัวเลข
- **ผู้ชนะ**: ดาวตก, ดอกไม้ไฟ, ลูกโป่ง, ประกายไฟ

## 🛡️ การใช้งาน Safeguards

### Test Mode (โหมดทดสอบ):
1. เปิด/ปิดผ่าน **Toggle Switch** ที่หัวหน้า Dashboard
2. เมื่อเปิด: แถบเหลืองจะแสดงตลอดเวลา
3. การจับรางวัลจะ**ไม่ถูกบันทึก**ลงฐานข้อมูล
4. ผลลัพธ์จะแสดง "🧪 ผลทดสอบ!" แทน
5. ใช้สำหรับทดสอบระบบก่อนงานจริง

### Undo Last Draw (ยกเลิกครั้งล่าสุด):
1. ปุ่ม **"↶ ยกเลิกครั้งล่าสุด"** จะปรากฏเมื่อมีประวัติ
2. กดปุ่มและยืนยันการกระทำ
3. ระบบจะ:
   - ลบประวัติการจับล่าสุด
   - คืนจำนวนรางวัล (โหมดคลาสสิก)
   - คืนสถานะผู้เข้าร่วม
4. ใช้เมื่อเกิดข้อผิดพลาดในงานจริง

## 🎯 ระบบสมบูรณ์แล้ว!

LuckyDraw System v1.6 พัฒนาครบทุก Phase ตามพิมพ์เขียวสถาปัตยกรรม พร้อมใช้งานในงานจริง!