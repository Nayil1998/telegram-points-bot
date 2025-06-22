from telethon import TelegramClient, functions
import asyncio
import os

api_id = 21716308
api_hash = 'e79a1356cefce48b9ae5e83d89b978f0'

client = TelegramClient('userbot', api_id, api_hash)

async def change_photo(photo_path):
    if not os.path.exists(photo_path):
        print(f"❌ الملف {photo_path} غير موجود في المجلد.")
        return

    print(f"⏳ جاري تعيين الصورة: {photo_path} ...")
    await client(functions.photos.UploadProfilePhotoRequest(
        file=await client.upload_file(photo_path)
    ))
    print(f"✅ تم تعيين الصورة بنجاح: {photo_path}")

async def main():
    choice = input("🟢 اكتب (start) أو (stop) لتغيير الصورة: ").strip().lower()

    if choice == "start":
        await change_photo("Start_Bot.jpg")
    elif choice == "stop":
        await change_photo("Stop_Bot.jpg")
    else:
        print("❌ خيار غير صحيح. الرجاء كتابة start أو stop فقط.")

with client:
    client.loop.run_until_complete(main())