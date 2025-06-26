from flask import Flask, request
import telebot

# التوكن مكتوب مباشرة كمثال
API_TOKEN = 7640107599:AAHWD3bVRu_5u9aeFmnAet5IltiZiJzRK_M'
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

# هذا المسار Telegram بيزوره للتأكد من جاهزية البوت
@app.route("/", methods=["GET"])
def index():
    return "✅ Bot is running!", 200

# هذا المسار Telegram بيرسل له التحديثات (Webhook)
@app.route("/7640107599:AAHj39sJCa6-PgWrL_JwToKAriESzpFvnm8", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

if __name__ == "__main__":
    # إزالة أي Webhook قديم
    bot.remove_webhook()

    # تعيين Webhook على رابط التطبيق + التوكن
    bot.set_webhook(url="https://telegram-points-bot.onrender.com/7640107599:AAHj39sJCa6-PgWrL_JwToKAriESzpFvnm8")

    # تشغيل السيرفر على Render
    app.run(host="0.0.0.0", port=10000)