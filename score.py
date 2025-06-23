import telebot
import json
import os
import re
import random
from telebot import types

API_TOKEN = '7886404694:AAGN-1PrEB6pA4fW1XoPGMOa0llIuTfMIH4'
bot = telebot.TeleBot(API_TOKEN)

DB_FILE = "points.json"
TEMPLATE_FILE = "template.txt"
TEMPLATES_FILE = "templates.json"
DEFAULT_TEMPLATE = "✿🧸.݁𝗣𝗢𝗜𝗡𝗧𝗦 ⁞‏"

all_points = {}
random_orders = {}
adding_to_raffle = set()
adding_to_points = set()
adding_to_normal = set()
editing_raffle = set()
editing_points = set()
random_order_mode = set()

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

if not os.path.exists(TEMPLATES_FILE):
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump([DEFAULT_TEMPLATE], f, ensure_ascii=False, indent=2)

if not os.path.exists(TEMPLATE_FILE):
    with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_TEMPLATE)

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_points():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_points, f, ensure_ascii=False, indent=2)

def load_template():
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip() or DEFAULT_TEMPLATE
    return DEFAULT_TEMPLATE

def set_current_template(template: str):
    with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
        f.write(template.strip())

def load_templates():
    try:
        if os.path.exists(TEMPLATES_FILE):
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return [DEFAULT_TEMPLATE]

def save_templates(templates: list):
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

def add_new_template(template):
    templates = load_templates()
    if template not in templates:
        templates.append(template)
        save_templates(templates)

def to_superscript(n: int) -> str:
    superscript_map = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", 
        "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", 
        "8": "⁸", "9": "⁹"
    }
    return "".join(superscript_map.get(d, d) for d in str(n))

all_points = load_data()

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 إدارة النقاط", "🎲 إدارة القرعة")
    keyboard.row("📝 إدارة القوالب", "⚙️ الإعدادات")
    bot.send_message(message.chat.id, "🎉 أهلاً بك في بوت النقاط! اختر القائمة:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "📊 إدارة النقاط")
def points_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🎯 تسجيل بنقاط", "📝 تسجيل عادي")
    keyboard.row("📊 عرض النقاط", "🏆 عرض الفائزين")
    keyboard.row("➖ خصم نقطة", "🧹 مسح النقاط")
    keyboard.row("📋 قائمة التسجيل العادي", "✏️ تعديل المشاركين")
    keyboard.row("🔙 رجوع")
    bot.send_message(message.chat.id, "📊 قائمة إدارة النقاط:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "✏️ تعديل المشاركين" and str(m.chat.id) not in editing_raffle)
def start_editing_points(message):
    chat_id = str(message.chat.id)
    editing_points.add(chat_id)
    
    if chat_id not in all_points or not all_points[chat_id]:
        bot.reply_to(message, "لا يوجد مشاركين لتعديلهم")
        editing_points.discard(chat_id)
        return
    
    participants = "\n".join([f"@{u} ({p} نقطة)" for u, p in all_points[chat_id].items()])
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("➕ إضافة", "➖ حذف")
    keyboard.row("📊 تعديل النقاط")
    keyboard.row("🔙 رجوع")
    
    bot.send_message(message.chat.id, f"✏️ وضع التعديل:\nالمشاركون الحاليون:\n{participants}\n\nاستخدم الأزرار للإضافة/الحذف/تعديل النقاط:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: str(m.chat.id) in editing_points)
def handle_points_edits(message):
    chat_id = str(message.chat.id)
    
    if message.text == "➕ إضافة":
        msg = bot.reply_to(message, "أرسل اسم المستخدم للإضافة (بدون @):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_add_participant_points)
    elif message.text == "➖ حذف":
        msg = bot.reply_to(message, "أرسل اسم المستخدم للحذف (بدون @):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_remove_participant_points)
    elif message.text == "📊 تعديل النقاط":
        msg = bot.reply_to(message, "أرسل اسم المستخدم لتعديل نقاطه (بدون @):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_ask_points_amount)
    elif message.text == "🔙 رجوع":
        editing_points.discard(chat_id)
        points_menu(message)

def process_add_participant_points(message):
    chat_id = str(message.chat.id)
    username = message.text.strip().replace("@", "")
    
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        bot.reply_to(message, "صيغة اسم المستخدم غير صالحة")
        start_editing_points(message)
        return
    
    if chat_id not in all_points:
        all_points[chat_id] = {}
    
    if username in all_points[chat_id]:
        bot.reply_to(message, f"@{username} موجود بالفعل")
    else:
        all_points[chat_id][username] = 0
        save_points()
        bot.reply_to(message, f"✅ تمت إضافة @{username} بنجاح")
    
    start_editing_points(message)

def process_remove_participant_points(message):
    chat_id = str(message.chat.id)
    username = message.text.strip().replace("@", "")
    
    if chat_id not in all_points or username not in all_points[chat_id]:
        bot.reply_to(message, f"@{username} غير موجود في المشاركين")
        start_editing_points(message)
        return
    
    del all_points[chat_id][username]
    save_points()
    bot.reply_to(message, f"✅ تم حذف @{username} بنجاح")
    start_editing_points(message)

def process_ask_points_amount(message, username=None):
    chat_id = str(message.chat.id)
    if username is None:
        username = message.text.strip().replace("@", "")
        
        if chat_id not in all_points or username not in all_points[chat_id]:
            bot.reply_to(message, f"@{username} غير موجود في المشاركين")
            start_editing_points(message)
            return
    
    msg = bot.reply_to(message, f"أدخل عدد النقاط الجديد لـ @{username}:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_update_points, username)

def process_update_points(message, username):
    chat_id = str(message.chat.id)
    try:
        points = int(message.text.strip())
        if points < 0:
            raise ValueError
    except:
        bot.reply_to(message, "❗ يرجى إدخال رقم صحيح موجب")
        start_editing_points(message)
        return
    
    all_points[chat_id][username] = points
    save_points()
    bot.reply_to(message, f"✅ تم تحديث نقاط @{username} إلى {points}")
    start_editing_points(message)

@bot.message_handler(func=lambda m: m.text == "📋 قائمة التسجيل العادي")
def show_normal_registered(message):
    try:
        chat_id = str(message.chat.id)
        
        if chat_id not in all_points or not all_points[chat_id]:
            bot.reply_to(message, "❗ لا يوجد مسجلين حتى الآن")
            return
        
        normal_participants = [user for user, points in all_points[chat_id].items() if points == 0]
        
        if not normal_participants:
            bot.reply_to(message, "❗ لا يوجد مشاركين مسجلين تسجيلاً عادياً")
            return
        
        count = len(normal_participants)
        header = "📋 قائمة المسجلين تسجيلاً عادياً\n━━━━━━━━━━━━━━"
        footer = f"━━━━━━━━━━━━━━\n🎉 {count} مشارك"
        
        chunk_size = 50
        chunks = [normal_participants[i:i + chunk_size] for i in range(0, len(normal_participants), chunk_size)]
        
        for chunk in chunks:
            participants_list = "\n".join([f"@{user}" for user in chunk])
            bot.send_message(message.chat.id, f"{header}\n{participants_list}\n{footer}")
            
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "📂 عرض القوالب")
def show_templates_button(message):
    templates = load_templates()
    if not templates:
        bot.reply_to(message, "❗ لا توجد قوالب محفوظة")
        return

    markup = types.InlineKeyboardMarkup()
    for idx, template in enumerate(templates):
        btn_text = template[:20] + "..." if len(template) > 20 else template
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"tpl_{idx}"))
    bot.send_message(message.chat.id, "📂 اختر أحد القوالب التالية:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tpl_"))
def handle_template_selection(call):
    try:
        idx = int(call.data.split("_")[1])
        templates = load_templates()
        
        if 0 <= idx < len(templates):
            template = templates[idx]
            set_current_template(template)
            bot.answer_callback_query(call.id, text="✅ تم اختيار القالب")
            bot.edit_message_text(chat_id=call.message.chat.id, 
                                message_id=call.message.message_id,
                                text=f"✅ تم اختيار القالب:\n{template}")
        else:
            bot.answer_callback_query(call.id, text="⚠️ القالب غير موجود")
    except:
        bot.answer_callback_query(call.id, text="⚠️ حدث خطأ")

@bot.message_handler(func=lambda m: m.text == "🎲 إدارة القرعة")
def raffle_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🎲 تسجيل قرعة", "📋 قائمة المسجلين")
    keyboard.row("✏️ تعديل المشاركين", "🎲 سحب الفائزين")
    keyboard.row("🔀 ترتيب عشوائي", "🧹 مسح الكل")
    keyboard.row("🔙 رجوع")
    bot.send_message(message.chat.id, "🎲 قائمة إدارة القرعة:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "✏️ تعديل المشاركين" and str(m.chat.id) not in editing_points)
def start_editing_raffle(message):
    chat_id = str(message.chat.id)
    editing_raffle.add(chat_id)
    
    if chat_id not in all_points or not all_points[chat_id]:
        bot.reply_to(message, "لا يوجد مشاركين لتعديلهم")
        editing_raffle.discard(chat_id)
        return
    
    participants = "\n".join([f"@{u}" for u in all_points[chat_id].keys()])
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("➕ إضافة", "➖ حذف")
    keyboard.row("🔙 رجوع")
    
    bot.send_message(message.chat.id, f"✏️ وضع التعديل:\nالمشاركون الحاليون:\n{participants}\n\nاستخدم الأزرار للإضافة/الحذف:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: str(m.chat.id) in editing_raffle)
def handle_raffle_edits(message):
    chat_id = str(message.chat.id)
    
    if message.text == "➕ إضافة":
        msg = bot.reply_to(message, "أرسل اسم المستخدم للإضافة (بدون @):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_add_participant)
    elif message.text == "➖ حذف":
        msg = bot.reply_to(message, "أرسل اسم المستخدم للحذف (بدون @):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_remove_participant)
    elif message.text == "🔙 رجوع":
        editing_raffle.discard(chat_id)
        raffle_menu(message)

def process_add_participant(message):
    chat_id = str(message.chat.id)
    username = message.text.strip().replace("@", "")
    
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        bot.reply_to(message, "صيغة اسم المستخدم غير صالحة")
        start_editing_raffle(message)
        return
    
    if chat_id not in all_points:
        all_points[chat_id] = {}
    
    if username in all_points[chat_id]:
        bot.reply_to(message, f"@{username} موجود بالفعل")
    else:
        all_points[chat_id][username] = 0
        save_points()
        bot.reply_to(message, f"✅ تمت إضافة @{username} بنجاح")
    
    start_editing_raffle(message)

def process_remove_participant(message):
    chat_id = str(message.chat.id)
    username = message.text.strip().replace("@", "")
    
    if chat_id not in all_points or username not in all_points[chat_id]:
        bot.reply_to(message, f"@{username} غير موجود في المشاركين")
        start_editing_raffle(message)
        return
    
    del all_points[chat_id][username]
    save_points()
    bot.reply_to(message, f"✅ تم حذف @{username} بنجاح")
    start_editing_raffle(message)

@bot.message_handler(func=lambda m: m.text == "📝 إدارة القوالب")
def templates_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("➕ إضافة قالب", "📂 عرض القوالب")
    keyboard.row("🗑️ حذف قالب", "📌 تعيين قالب")
    keyboard.row("🔙 رجوع")
    bot.send_message(message.chat.id, "📝 قائمة إدارة القوالب:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "⚙️ الإعدادات")
def settings_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🎥 شرح البوت", "🔄 تحديث البوت")
    keyboard.row("🔙 رجوع")
    bot.send_message(message.chat.id, "⚙️ قائمة الإعدادات:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "🔙 رجوع")
def back_to_main(message):
    chat_id = str(message.chat.id)
    adding_to_raffle.discard(chat_id)
    adding_to_points.discard(chat_id)
    adding_to_normal.discard(chat_id)
    editing_raffle.discard(chat_id)
    editing_points.discard(chat_id)
    random_order_mode.discard(chat_id)
    handle_start(message)

@bot.message_handler(func=lambda m: m.text == "🔀 ترتيب عشوائي")
def random_order_menu(message):
    chat_id = str(message.chat.id)
    random_order_mode.add(chat_id)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🔄 توليد ترتيب", "📋 عرض الترتيب")
    keyboard.row("🔙 رجوع")
    
    bot.send_message(message.chat.id, "🔀 وضع الترتيب العشوائي:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "🔄 توليد ترتيب" and str(m.chat.id) in random_order_mode)
def generate_random_order(message):
    chat_id = str(message.chat.id)
    
    if chat_id not in all_points or not all_points[chat_id]:
        bot.reply_to(message, "لا يوجد مشاركين متاحين")
        return
    
    participants = list(all_points[chat_id].keys())
    random.shuffle(participants)
    random_orders[chat_id] = participants
    show_order(message, participants)

@bot.message_handler(func=lambda m: m.text == "📋 عرض الترتيب" and str(m.chat.id) in random_order_mode)
def show_random_order(message):
    chat_id = str(message.chat.id)
    
    if chat_id not in random_orders:
        bot.reply_to(message, "لا يوجد ترتيب متاح، يرجى توليد ترتيب أولاً")
        return
    
    show_order(message, random_orders[chat_id])

def show_order(message, participants):
    order_list = "\n".join([f"{i+1}. @{username}" for i, username in enumerate(participants)])
    bot.reply_to(message, f"🔀 الترتيب العشوائي:\n\n{order_list}\n\nالمجموع: {len(participants)} مشارك")

@bot.message_handler(func=lambda m: m.text == "🎲 تسجيل قرعة")
def start_adding_to_raffle(message):
    chat_id = str(message.chat.id)
    adding_to_raffle.add(chat_id)
    msg = bot.reply_to(message, "✏️ أرسل اسم المستخدم للتسجيل في القرعة (استخدم زر 🔙 رجوع للخروج):")
    bot.register_next_step_handler(msg, process_raffle_register_loop)

def process_raffle_register_loop(message):
    chat_id = str(message.chat.id)
    
    if message.text == "🔙 رجوع":
        adding_to_raffle.discard(chat_id)
        raffle_menu(message)
        return
    
    username = message.text.strip().replace("@", "")
    
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        msg = bot.reply_to(message, "❗ يرجى إرسال يوزر إنجليزي صحيح")
        bot.register_next_step_handler(msg, process_raffle_register_loop)
        return
    
    if chat_id not in all_points:
        all_points[chat_id] = {}
    
    if username in all_points[chat_id]:
        bot.reply_to(message, f"⚠️ المستخدم @{username} مسجل بالفعل")
    else:
        all_points[chat_id][username] = 0
        save_points()
        bot.reply_to(message, f"✅ تم تسجيل @{username} في القرعة")
    
    msg = bot.reply_to(message, "✏️ أرسل اسم مستخدم آخر:")
    bot.register_next_step_handler(msg, process_raffle_register_loop)

@bot.message_handler(func=lambda m: m.text == "🎯 تسجيل بنقاط")
def start_adding_points(message):
    chat_id = str(message.chat.id)
    adding_to_points.add(chat_id)
    msg = bot.reply_to(message, "✏️ أرسل اسم المستخدم للتسجيل مع إضافة نقطة (استخدم زر 🔙 رجوع للخروج):")
    bot.register_next_step_handler(msg, process_points_register_loop)

def process_points_register_loop(message):
    chat_id = str(message.chat.id)
    
    if message.text == "🔙 رجوع":
        adding_to_points.discard(chat_id)
        points_menu(message)
        return
    
    username = message.text.strip().replace("@", "")
    
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        msg = bot.reply_to(message, "❗ يرجى إرسال يوزر إنجليزي صحيح")
        bot.register_next_step_handler(msg, process_points_register_loop)
        return
    
    if chat_id not in all_points:
        all_points[chat_id] = {}
    
    all_points[chat_id][username] = all_points[chat_id].get(username, 0) + 1
    save_points()
    bot.reply_to(message, f"✅ تم تسجيل @{username} مع إضافة نقطة\n{display_points(chat_id)}")
    
    msg = bot.reply_to(message, "✏️ أرسل اسم مستخدم آخر:")
    bot.register_next_step_handler(msg, process_points_register_loop)

@bot.message_handler(func=lambda m: m.text == "📝 تسجيل عادي")
def start_adding_normal(message):
    chat_id = str(message.chat.id)
    adding_to_normal.add(chat_id)
    msg = bot.reply_to(message, "✏️ أرسل اسم المستخدم للتسجيل بدون نقاط (استخدم زر 🔙 رجوع للخروج):")
    bot.register_next_step_handler(msg, process_normal_register_loop)

def process_normal_register_loop(message):
    chat_id = str(message.chat.id)
    
    if message.text == "🔙 رجوع":
        adding_to_normal.discard(chat_id)
        points_menu(message)
        return
    
    username = message.text.strip().replace("@", "")
    
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        msg = bot.reply_to(message, "❗ يرجى إرسال يوزر إنجليزي صحيح")
        bot.register_next_step_handler(msg, process_normal_register_loop)
        return
    
    if chat_id not in all_points:
        all_points[chat_id] = {}
    
    if username in all_points[chat_id]:
        bot.reply_to(message, f"⚠️ المستخدم @{username} مسجل بالفعل")
    else:
        all_points[chat_id][username] = 0
        save_points()
        bot.reply_to(message, f"✅ تم تسجيل @{username} بدون نقاط")
    
    msg = bot.reply_to(message, "✏️ أرسل اسم مستخدم آخر:")
    bot.register_next_step_handler(msg, process_normal_register_loop)

@bot.message_handler(func=lambda m: m.text == "📋 قائمة المسجلين")
def show_registered_list(message):
    chat_id = str(message.chat.id)
    
    if chat_id not in all_points or not all_points[chat_id]:
        bot.reply_to(message, "❗ لا يوجد مسجلين حتى الآن")
        return
    
    participants = list(all_points[chat_id].keys())
    count = len(participants)
    
    header = "✨ قائمة المشاركين ✨\n━━━━━━━━━━━━━━"
    footer = f"━━━━━━━━━━━━━━\n🎉 {count} مشارك"
    
    chunk_size = 50
    chunks = [participants[i:i + chunk_size] for i in range(0, len(participants), chunk_size)]
    
    for chunk in chunks:
        participants_list = "\n".join([f"@{user}" for user in chunk])
        message_text = f"{header}\n{participants_list}\n{footer}" if chunk == chunks[-1] else f"{header}\n{participants_list}"
        bot.send_message(message.chat.id, message_text)

def display_points(chat_id: str) -> str:
    template = load_template()
    chat_points = all_points.get(chat_id, {})
    sorted_users = sorted(chat_points.items(), key=lambda x: x[1], reverse=True)
    users = [f"@{u}{to_superscript(c)}" for u, c in sorted_users]
    return template + "\n" + " | ".join(users) if users else "لا توجد نقاط بعد"

@bot.message_handler(func=lambda m: m.text == "📊 عرض النقاط")
def show_points(message):
    chat_id = str(message.chat.id)
    bot.reply_to(message, display_points(chat_id))

@bot.message_handler(func=lambda m: m.text == "🏆 عرض الفائزين")
def ask_winners_count(message):
    msg = bot.reply_to(message, "🎯 كم عدد الفائزين الذين تريد استخراجهم؟ (مثال: 3)")
    bot.register_next_step_handler(msg, process_winners_count)

def process_winners_count(message):
    chat_id = str(message.chat.id)
    text = message.text.strip()
    
    if not text.isdigit() or int(text) <= 0:
        bot.reply_to(message, "❗ يرجى إدخال رقم صحيح موجب")
        return
    
    num = int(text)
    chat_points = all_points.get(chat_id, {})
    
    if not chat_points:
        bot.reply_to(message, "❗ لا توجد نقاط مسجلة")
        return
    
    sorted_users = sorted(chat_points.items(), key=lambda x: x[1], reverse=True)
    top_users = sorted_users[:num]
    
    title = "🏆 الفائز:" if len(top_users) == 1 else "🏆 الفائزون:"
    result = "\n".join([f"{i+1}. @{u} {to_superscript(p)}" for i, (u, p) in enumerate(top_users)])
    bot.reply_to(message, f"{title}\n{result}")

@bot.message_handler(func=lambda m: m.text == "🎲 سحب الفائزين")
def ask_raffle_winners_count(message):
    chat_id = str(message.chat.id)
    
    if chat_id not in all_points or not all_points[chat_id]:
        bot.reply_to(message, "❗ لا يوجد مشاركين في القرعة")
        return
    
    msg = bot.reply_to(message, "🎯 كم عدد الفائزين في السحب؟ (أدخل رقم)")
    bot.register_next_step_handler(msg, process_raffle_winners_count)

def process_raffle_winners_count(message):
    chat_id = str(message.chat.id)
    text = message.text.strip()
    
    if not text.isdigit() or int(text) <= 0:
        bot.reply_to(message, "❗ يرجى إدخال رقم صحيح موجب")
        return
    
    winners_count = int(text)
    participants = list(all_points.get(chat_id, {}).keys())
    
    if winners_count > len(participants):
        bot.reply_to(message, f"❗ عدد الفائزين أكبر من عدد المشاركين ({len(participants)})")
        return
    
    winners = random.sample(participants, winners_count)
    result = "\n".join([f"🏅 @{winner}" for winner in winners])
    bot.reply_to(message, f"🎉 الفائزون:\n{result}")

@bot.message_handler(func=lambda m: m.text == "🧹 مسح النقاط")
def clear_points(message):
    chat_id = str(message.chat.id)
    all_points[chat_id] = {}
    save_points()
    bot.reply_to(message, "✅ تم مسح جميع النقاط")

@bot.message_handler(func=lambda m: m.text == "🧹 مسح الكل")
def clear_all(message):
    chat_id = str(message.chat.id)
    all_points[chat_id] = {}
    if chat_id in random_orders:
        del random_orders[chat_id]
    save_points()
    bot.reply_to(message, "✅ تم مسح جميع البيانات")

@bot.message_handler(func=lambda m: m.text == "➖ خصم نقطة")
def ask_user_to_deduct(message):
    msg = bot.reply_to(message, "✏️ أرسل اسم المستخدم لخصم نقطة (بدون @):")
    bot.register_next_step_handler(msg, process_deduction)

def process_deduction(message):
    chat_id = str(message.chat.id)
    username = message.text.strip().replace("@", "")
    
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        bot.reply_to(message, "❗ يرجى إرسال يوزر إنجليزي صحيح")
        return
    
    if chat_id not in all_points or username not in all_points[chat_id]:
        bot.reply_to(message, "⚠️ هذا المستخدم لا يملك نقاط")
        return
    
    all_points[chat_id][username] -= 1
    if all_points[chat_id][username] <= 0:
        del all_points[chat_id][username]
    save_points()
    bot.reply_to(message, display_points(chat_id))

@bot.message_handler(func=lambda m: m.text == "➕ إضافة قالب")
def ask_for_new_template(message):
    msg = bot.reply_to(message, "✏️ أرسل النص الجديد للقالب:")
    bot.register_next_step_handler(msg, save_new_template)

def save_new_template(message):
    new_template = message.text.strip()
    if not new_template:
        bot.reply_to(message, "❗ لم يتم إرسال أي نص")
        return
    
    add_new_template(new_template)
    bot.reply_to(message, f"✅ تم حفظ القالب:\n{new_template}")

@bot.message_handler(func=lambda m: m.text == "🗑️ حذف قالب")
def remove_template_button(message):
    current = load_template()
    templates = load_templates()

    if current == DEFAULT_TEMPLATE:
        bot.reply_to(message, "⚠️ لا يمكن حذف القالب الافتراضي")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("✅ تأكيد الحذف", "❌ إلغاء")
    msg = bot.reply_to(message, f"⚠️ تأكيد حذف القالب الحالي؟\n{current}", reply_markup=markup)
    bot.register_next_step_handler(msg, confirm_template_deletion, current, templates)

def confirm_template_deletion(message, current_template, templates):
    chat_id = str(message.chat.id)
    if message.text == "✅ تأكيد الحذف":
        if current_template in templates:
            templates.remove(current_template)
            save_templates(templates)
            set_current_template(DEFAULT_TEMPLATE)
            bot.send_message(chat_id, f"✅ تم الحذف، القالب الحالي:\n{DEFAULT_TEMPLATE}")
    else:
        bot.send_message(chat_id, "❌ تم الإلغاء")
    
    handle_start(message)

@bot.message_handler(func=lambda m: m.text == "📌 تعيين قالب")
def ask_template_to_set(message):
    templates = load_templates()
    if not templates:
        bot.reply_to(message, "❗ لا توجد قوالب محفوظة")
        return

    markup = types.InlineKeyboardMarkup()
    for idx, template in enumerate(templates):
        btn_text = template[:20] + "..." if len(template) > 20 else template
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"tpl_{idx}"))
    bot.send_message(message.chat.id, "📌 اختر قالباً لتعيينه:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎥 شرح البوت")
def send_bot_tutorial(message):
    bot.reply_to(message, "شرح استخدام البوت:\n\n"
                         "- 📊 إدارة النقاط: لتسجيل وعرض النقاط\n"
                         "- 🎲 إدارة القرعة: لسحب الفائزين والترتيب العشوائي\n"
                         "- 📝 إدارة القوالب: لتخصيص شكل عرض النقاط\n"
                         "- ⚙️ الإعدادات: للتحكم بالإعدادات العامة\n"
                         "- 📋 قائمة التسجيل العادي: لعرض المسجلين بدون نقاط")

@bot.message_handler(func=lambda m: m.text == "🔄 تحديث البوت")
def update_bot(message):
    bot.reply_to(message, "✅ تم تحديث البوت بنجاح")
    handle_start(message)

if __name__ == '__main__':
    all_points = load_data()
    print("✅ تم تشغيل البوت بنجاح...")
    bot.infinity_polling()