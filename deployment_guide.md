# 🚀 LuckyDraw Deployment Guide for PythonAnywhere

## ขั้นตอนการ Deploy บน PythonAnywhere

### 1. 📁 Upload โปรเจกต์

1. เข้าสู่ PythonAnywhere Console: https://www.pythonanywhere.com/user/Sarayutp/consoles/
2. เปิด **Bash console**
3. Clone โปรเจกต์จาก GitHub:

```bash
cd ~
git clone https://github.com/Sarayutp/LuckyDraw.git
cd LuckyDraw
```

### 2. 🐍 ตั้งค่า Virtual Environment

```bash
# สร้าง virtual environment
python3.11 -m venv mysite-virtualenv

# เปิดใช้งาน virtual environment
source mysite-virtualenv/bin/activate

# อัพเกรด pip
pip install --upgrade pip

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### 3. 🌐 ตั้งค่า Web App

1. ไปที่ **Web** tab: https://www.pythonanywhere.com/user/Sarayutp/webapps/
2. คลิก **"Add a new web app"**
3. เลือก domain: `sarayutp.pythonanywhere.com`
4. เลือก **"Manual configuration"**
5. เลือก **Python 3.11**

### 4. ⚙️ กำหนดค่า Web App

ใน **Web** tab ให้ตั้งค่าดังนี้:

#### Source code:
```
/home/Sarayutp/LuckyDraw
```

#### Working directory:
```
/home/Sarayutp/LuckyDraw
```

#### WSGI configuration file:
```
/home/Sarayutp/LuckyDraw/wsgi.py
```

#### Virtual environment:
```
/home/Sarayutp/LuckyDraw/mysite-virtualenv
```

### 5. 🗃️ ตั้งค่า Static Files

ใน **Static files** section:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/Sarayutp/LuckyDraw/static/` |

### 6. 🔧 แก้ไข WSGI Configuration

1. คลิกที่ WSGI configuration file link
2. ลบเนื้อหาเดิมทั้งหมด
3. แทนที่ด้วย:

```python
import sys
import os

# Add your project directory to sys.path
project_home = '/home/Sarayutp/LuckyDraw'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app import app as application

if __name__ == "__main__":
    application.run()
```

### 7. 🎯 สร้างฐานข้อมูล

ใน Bash console:

```bash
cd ~/LuckyDraw
source mysite-virtualenv/bin/activate
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created successfully!')"
```

### 8. 🔄 Reload Web App

1. กลับไปที่ **Web** tab
2. คลิก **"Reload sarayutp.pythonanywhere.com"**

### 9. ✅ ทดสอบ

เปิดเว็บไซต์ที่: **https://sarayutp.pythonanywhere.com**

## 🐛 Troubleshooting

### ถ้ามี Error:

1. ดู **Error log** ใน Web tab
2. ดู **Server log** ใน Web tab

### คำสั่งที่มีประโยชน์:

```bash
# ดู log
tail -f /var/log/sarayutp.pythonanywhere.com.error.log

# เช็ค dependencies
pip list

# ทดสอบ import
python -c "from app import app; print('Import successful!')"
```

## 🔄 การอัพเดท

เมื่อต้องการอัพเดทโค้ด:

```bash
cd ~/LuckyDraw
git pull origin main
# หรือ
git pull origin feature/next-phase
```

จากนั้นคลิก **Reload** ใน Web tab

## 📱 URL สำหรับเข้าใช้งาน

- **Production**: https://sarayutp.pythonanywhere.com
- **Admin Panel**: https://sarayutp.pythonanywhere.com (หน้าแรก)

## 🔐 Security Notes

- ฐานข้อมูล SQLite จะถูกสร้างที่ `/home/Sarayutp/LuckyDraw/luckydraw.db`
- ไฟล์อัพโหลดจะอยู่ที่ `/home/Sarayutp/LuckyDraw/uploads/`
- ตรวจสอบให้แน่ใจว่า SECRET_KEY ถูกตั้งค่าอย่างปลอดภัย

## 📞 Support

หากมีปัญหา สามารถตรวจสอบได้ที่:
- PythonAnywhere Help: https://help.pythonanywhere.com/
- Forums: https://www.pythonanywhere.com/forums/