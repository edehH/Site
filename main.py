from pywebio import start_server
from pywebio.input import input, input_group, radio
from pywebio.output import put_text, put_html, put_table, popup, toast, clear, put_buttons
from datetime import datetime, timedelta
import sqlite3
import os  # استيراد مكتبة os للحصول على المنفذ من البيئة

# الاتصال بقاعدة البيانات مع تفعيل check_same_thread=False
conn = sqlite3.connect("bookings.db", check_same_thread=False)
cursor = conn.cursor()

# إنشاء جدول للحجوزات إذا لم يكن موجودًا
cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    time TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )''')
conn.commit()

ADMIN_EMAIL = "edehwww@gmail.com"  # البريد الخاص بالمشرف

def remove_expired_bookings():
    """إزالة الحجوزات التي مر عليها 24 ساعة من تاريخ إنشائها."""
    now = datetime.now()
    cursor.execute("SELECT id, created_at FROM bookings")
    expired_bookings = cursor.fetchall()
    for booking in expired_bookings:
        created_at = datetime.strptime(booking[1], "%Y-%m-%d %H:%M:%S")
        if now - created_at > timedelta(hours=24):
            cursor.execute("DELETE FROM bookings WHERE id = ?", (booking[0],))
            conn.commit()

def delete_booking(index, is_admin):
    """يسمح بالحذف فقط إذا كان المستخدم مشرف"""
    if is_admin:
        cursor.execute("DELETE FROM bookings WHERE id = ?", (index,))
        conn.commit()
        toast("✅ تم حذف الحجز بنجاح!", color="warn")
    else:
        toast("❌ ليس لديك صلاحية لحذف الحجوزات!", color="error")
    clear()
    App()

def get_bookings():
    """جلب الحجوزات من قاعدة البيانات."""
    cursor.execute("SELECT id, user, phone, time FROM bookings")
    return cursor.fetchall()

def add_booking(user, phone, time):
    """إضافة حجز جديد إلى قاعدة البيانات."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO bookings (user, phone, time, created_at) VALUES (?, ?, ?, ?)", 
                   (user, phone, time, created_at))
    conn.commit()

def App():
    remove_expired_bookings()

    # عرض صورة كواجهة للموقع
    put_html('<div style="text-align:center;">'
             '<img src="https://i.postimg.cc/NMY7p2Jm/IMG-20250308-WA0003.jpg" '
             'style="width:100%; max-width: 800px; border-radius: 10px;" />'
             '</div>')

    popup("🎉 مرحبا بكم في موقعنا لحجز المباريات 🎉")

    # اختيار دور المستخدم: مشرف أم زائر
    role = radio("حدد نوع المستخدم", options=["أنا مشرف", "متابعة كزائر"])
    is_admin = False
    if role == "أنا مشرف":
        admin_email = input("📧 أدخل بريد المشرف للتحقق", required=True)
        if admin_email == ADMIN_EMAIL:
            is_admin = True
            toast("🎉 مرحباً مشرف الموقع!", color="success")
        else:
            toast("❌ بيانات المشرف غير صحيحة!", color="error")
    
    put_html('<center><h3>📅 المواعيد المحجوزة</h3></center>')
    bookings = get_bookings()
    if bookings:
        table_data = [['👤 الاسم', '📞 رقم الهاتف', '⏰ الوقت', '⚙ إجراء']]
        for booking in bookings:
            actions = put_buttons(["❌ حذف"], onclick=lambda x, idx=booking[0]: delete_booking(idx, is_admin)) if is_admin else "🚫"
            table_data.append([booking[1], booking[2], booking[3], actions])
        put_table(table_data)
    else:
        put_html('<center><p style="color:#3498db;">❌ لا يوجد حجوزات حتى الآن</p></center>')

    if is_admin:
        data = input_group("📝 حجز مباراة جديدة", [
            input('👤 ادخل اسم اللاعب', name='user', required=True),
            input('📞 ادخل رقم الهاتف', name='phone', required=True),
            input('⏰ ادخل الوقت الذي تريد الحجز فيه (مثال: 15:00)', name='time', required=True)
        ])
        cursor.execute("SELECT * FROM bookings WHERE time = ?", (data['time'],))
        existing_booking = cursor.fetchone()
        if existing_booking:
            toast("⚠ هذا الوقت محجوز بالفعل، يرجى اختيار وقت آخر!", color="error")
        else:
            add_booking(data['user'], data['phone'], data['time'])
            toast("✅ تمت إضافة الحجز بنجاح!", color="success")
        clear()
        App()
    else:
        # للزائرين ندمج رابط التواصل مع الواتساب
        put_html('''
            <center>
                <p>📲 للحجز، تواصل معنا ليتم عرضك في قائمة الحجوزات</p>
                <a href="https://wa.me/qr/L4HT5D4YTYDWO1" target="_blank" rel="noopener noreferrer"
                   style="text-decoration:none; color:#fff; background-color:#25D366; padding:10px 20px; border-radius:5px;">
                   اضغط هنا للتواصل والحجز
                </a>
            </center>
        ''')

# 🔹 تشغيل التطبيق على المنفذ الذي يحدده Render
PORT = int(os.getenv("PORT", 10000))  
start_server(App, port=PORT, debug=True)