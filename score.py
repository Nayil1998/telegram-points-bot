
import telebot
import json
import os
import re
from typing import Dict, Any
from telebot import types

API_TOKEN = '7640107599:AAFjRUgButnfq6t4_reOoz57aVxXsVQMfeY'
bot = telebot.TeleBot(API_TOKEN)

DB_FILE = "points.json"
TEMPLATE_FILE = "template.txt"
TEMPLATES_FILE = "templates.json"
DEFAULT_TEMPLATE = "✿🧸.݁𝗣𝗢𝗜𝗡𝗧𝗦 ⁞‏"

EXCLUDED_COMMANDS = ["/start", "/help", "/points", "/النقاط", "/فائزين", "/قالب"]

def load_data() -> Dict[str, Any]:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_points():
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(all_points, f, ensure_ascii=False, indent=2)

def load_template() -> str:
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() or DEFAULT_TEMPLATE
    return DEFAULT_TEMPLATE

def set_current_template(template: str):
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        f.write(template.strip())

def load_templates() -> list:
    try:
        if os.path.exists(TEMPLATES_FILE):
            with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception as e:
        print(f"[!] خطأ في قراءة templates.json: {e}")
    return [DEFAULT_TEMPLATE]

def save_templates(templates: list):
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

def add_new_template(template: str):
    templates = load_templates()
    if template not in templates:
        templates.append(template)
        save_templates(templates)
    set_current_template(template)

all_points = load_data()

def to_superscript(n: int) -> str:
    return str(n).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))

def display_points(chat_id: str) -> str:
    template = load_template()
    chat_points = all_points.get(chat_id, {})
    sorted_users = sorted(chat_points.items(), key=lambda x: x[1], reverse=True)
    users = [f"@{u}{to_superscript(c)}" for u, c in sorted_users]
    return template + "\n" + " | ".join(users) if users else "لا توجد نقاط بعد."

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 عرض النقاط", "🏆 عرض الفائزين")
    keyboard.row("🧹 مسح النقاط", "🗑️ إزالة القالب")
    keyboard.row("➖ خصم نقطة", "📂 عرض القوالب")
    keyboard.row("➕ إضافة قالب", "🎥 شرح البوت")
    bot.send_message(message.chat.id, "🎉 أهلاً بك في بوت النقاط!", reply_markup=keyboard)

@bot.message_handler(commands=['points', 'النقاط'])
def show_points(message):
    chat_id = str(message.chat.id)
    bot.reply_to(message, display_points(chat_id))

@bot.message_handler(commands=['قالب'])
def set_template(message):
    parts = message.text.split(" ", 1)
    if len(parts) == 2:
        new_template = parts[1].strip()
        add_new_template(new_template)
        bot.reply_to(message, f"✅ تم إضافة القالب واختياره:\n{new_template}")
    else:
        current = load_template()
        bot.reply_to(message, f"📌 القالب الحالي:\n{current}")

@bot.message_handler(commands=['فائزين'])
def ask_winners_count(message):
    msg = bot.reply_to(message, "🎯 كم عدد الفائزين الذين تريد استخراجهم؟ (مثال: 3)")
    bot.register_next_step_handler(msg, process_winners_count)

def process_winners_count(message):
    chat_id = str(message.chat.id)
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        bot.reply_to(message, "❗ يرجى إدخال رقم صحيح.")
        return

    num = int(text)
    chat_points = all_points.get(chat_id, {})
    if not chat_points:
        bot.reply_to(message, "❗ لا توجد نقاط بعد.")
        return

    sorted_users = sorted(chat_points.items(), key=lambda x: x[1], reverse=True)
    top_users = sorted_users[:num]
    if not top_users:
        bot.reply_to(message, "❗ لا يوجد فائزين.")
        return

    title = "🏆 *الفائز:*" if len(top_users) == 1 else "🏆 *الفائزين:*"
    result = "\n".join([f"{i+1}. @{u} {to_superscript(p)}" for i, (u, p) in enumerate(top_users)])
    bot.reply_to(message, f"{title}\n{result}", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🧹 مسح النقاط")
def clear_button(message):
    chat_id = str(message.chat.id)
    all_points[chat_id] = {}
    save_points()
    bot.reply_to(message, "✅ تم مسح قائمة النقاط لهذه المحادثة.")

@bot.message_handler(func=lambda m: m.text == "📊 عرض النقاط")
def show_points_button(message):
    show_points(message)

@bot.message_handler(func=lambda m: m.text == "🏆 عرض الفائزين")
def show_winners_button(message):
    ask_winners_count(message)

@bot.message_handler(func=lambda m: m.text == "🗑️ إزالة القالب")
def remove_template_button(message):
    current = load_template()
    templates = load_templates()

    if current != DEFAULT_TEMPLATE and current in templates:
        templates.remove(current)
        save_templates(templates)

    set_current_template(DEFAULT_TEMPLATE)
    bot.reply_to(message, f"✅ تم حذف القالب الحالي وإعادة القالب الافتراضي:\n{DEFAULT_TEMPLATE}")

@bot.message_handler(func=lambda m: m.text == "📂 عرض القوالب")
def show_templates_button(message):
    templates = load_templates()
    if not templates:
        bot.reply_to(message, "❗ لا توجد قوالب محفوظة.")
        return

    markup = types.InlineKeyboardMarkup()
    for idx, template in enumerate(templates, 1):
        markup.add(types.InlineKeyboardButton(f"📎 قالب {idx}", callback_data=f"set_template_{idx}"))

    bot.send_message(message.chat.id, "🧾 اختر أحد القوالب التالية:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_template_"))
def handle_template_selection(call):
    idx = int(call.data.split("_")[-1]) - 1
    templates = load_templates()

    if 0 <= idx < len(templates):
        selected_template = templates[idx]
        set_current_template(selected_template)
        bot.answer_callback_query(call.id, text="✅ تم اختيار القالب.")
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=f"✅ تم اختيار القالب:\n{selected_template}")
    else:
        bot.answer_callback_query(call.id, text="⚠️ قالب غير موجود.")

@bot.message_handler(func=lambda m: m.text == "➖ خصم نقطة")
def ask_user_to_deduct(message):
    msg = bot.reply_to(message, "✏️ أرسل اسم المستخدم الذي تريد خصم نقطة منه (مثال: @username)")
    bot.register_next_step_handler(msg, process_deduction)

def process_deduction(message):
    chat_id = str(message.chat.id)
    username = message.text.strip().replace("@", "")

    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        bot.reply_to(message, "❗ يرجى إرسال يوزر إنجليزي صحيح.")
        return

    if chat_id not in all_points or username not in all_points[chat_id]:
        bot.reply_to(message, "⚠️ هذا المستخدم لا يملك نقاط.")
        return

    all_points[chat_id][username] -= 1
    if all_points[chat_id][username] <= 0:
        del all_points[chat_id][username]

    save_points()
    bot.reply_to(message, display_points(chat_id))

@bot.message_handler(func=lambda m: m.text == "➕ إضافة قالب")
def ask_for_new_template(message):
    msg = bot.reply_to(message, "✏️ أرسل القالب الذي تريد حفظه.")
    bot.register_next_step_handler(msg, save_new_template)

def save_new_template(message):
    new_template = message.text.strip()
    if not new_template:
        bot.reply_to(message, "❗ لم يتم إرسال أي قالب.")
        return

    add_new_template(new_template)
    bot.reply_to(message, f"✅ تم حفظ القالب وتعيينه:\n{new_template}")

@bot.message_handler(func=lambda m: m.text and m.text.strip() not in [
    "📊 عرض النقاط", "🏆 عرض الفائزين", "🧹 مسح النقاط", "🗑️ إزالة القالب",
    "➖ خصم نقطة", "📂 عرض القوالب", "➕ إضافة قالب", "🎥 شرح البوت"
] and not m.text.startswith("/") and re.fullmatch(r'^[A-Za-z0-9_@]{3,34}$', m.text.strip()))
def handle_add_point(message):
    chat_id = str(message.chat.id)
    text = message.text.strip()
    username = text.replace("@", "").strip()

    if not re.fullmatch(r'^[A-Za-z0-9_]{3,32}$', username):
        bot.reply_to(message, "❗ يرجى إرسال يوزر إنجليزي صحيح.")
        return

    if chat_id not in all_points:
        all_points[chat_id] = {}

    all_points[chat_id][username] = all_points[chat_id].get(username, 0) + 1
    save_points()
    bot.reply_to(message, display_points(chat_id))


@bot.message_handler(func=lambda m: m.text == "🎥 شرح البوت")
def send_bot_tutorial(message):
    video_path = "tutorial.mp4"
    if os.path.exists(video_path):
        with open(video_path, "rb") as video:
            bot.send_chat_action(message.chat.id, 'upload_video')
            bot.send_video(message.chat.id, video, caption="🎬 شرح سريع لطريقة استخدام البوت.")
    else:
        bot.reply_to(message, "❗ لم يتم العثور على فيديو الشرح. تأكد من وجود ملف tutorial.mp4 في نفس مجلد البوت.")


if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
