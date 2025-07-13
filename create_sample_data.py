"""
สร้างข้อมูลตัวอย่างสำหรับทดสอบ LuckyDraw System
"""
from app import app
from models import db, Event, Participant, Prize
from datetime import datetime

def create_sample_data():
    with app.app_context():
        # สร้างตาราง
        db.create_all()
        
        # ลบข้อมูลเก่า (ถ้ามี)
        Event.query.delete()
        Participant.query.delete()
        Prize.query.delete()
        db.session.commit()
        
        # สร้างอีเวนต์ตัวอย่าง 1: Classic Mode
        classic_event = Event(
            name="งานปาร์ตี้ปีใหม่ บริษัท ABC",
            event_type="classic",
            created_at=datetime.utcnow()
        )
        db.session.add(classic_event)
        db.session.flush()  # Get ID
        
        # เพิ่มผู้เข้าร่วมสำหรับ Classic Event
        classic_participants = [
            "สมชาย ใจดี", "วรรณา สวยงาม", "ธนาคาร รวยมาก", 
            "สมหญิง น่ารัก", "ชัยชนะ กล้าหาญ", "วิภาวี เก่งมาก",
            "ประเสริฐ มั่นคง", "ดวงดาว สดใส", "สุกัญญา มีสุข",
            "วิทยา ฉลาด"
        ]
        
        for name in classic_participants:
            participant = Participant(name=name, event_id=classic_event.id)
            db.session.add(participant)
        
        # เพิ่มรางวัลสำหรับ Classic Event
        classic_prizes = [
            ("iPhone 15 Pro", 1),
            ("iPad Air", 2),
            ("AirPods Pro", 3),
            ("บัตรของขวัญ 5,000 บาท", 2),
            ("บัตรของขวัญ 1,000 บาท", 5)
        ]
        
        for prize_name, quantity in classic_prizes:
            prize = Prize(
                name=prize_name, 
                total_quantity=quantity,
                remaining_quantity=quantity,
                event_id=classic_event.id
            )
            db.session.add(prize)
        
        # สร้างอีเวนต์ตัวอย่าง 2: Exchange Mode
        exchange_event = Event(
            name="แลกเปลี่ยนของขวัญ Secret Santa",
            event_type="exchange",
            created_at=datetime.utcnow(),
            is_test_mode=True  # ตัวอย่างโหมดทดสอบ
        )
        db.session.add(exchange_event)
        db.session.flush()  # Get ID
        
        # เพิ่มผู้เข้าร่วมสำหรับ Exchange Event
        exchange_participants = [
            "อลิซ วันเดอร์", "บ็อบ บิลเดอร์", "ชาร์ลี ชาร์ม",
            "ไดอานา ดรีม", "เอ็ดเวิร์ด เอเลแกนซ์", "ฟิโอนา เฟียร์"
        ]
        
        for name in exchange_participants:
            participant = Participant(name=name, event_id=exchange_event.id)
            db.session.add(participant)
        
        # บันทึกข้อมูล
        db.session.commit()
        
        print("✅ สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว!")
        print(f"📋 อีเวนต์คลาสสิก ID: {classic_event.id}")
        print(f"🔗 http://localhost:5001/event/{classic_event.id}")
        print(f"🎁 อีเวนต์แลกเปลี่ยน ID: {exchange_event.id}")
        print(f"🔗 http://localhost:5001/event/{exchange_event.id}")

if __name__ == "__main__":
    create_sample_data()