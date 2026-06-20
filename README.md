# Group Resale Bot

A professional Telegram bot system for automated Telegram group resale — group catalog with pagination, purchase flow with admin approval, automatic buyer onboarding via Telethon, and a separate support bot with live admin chat relay. Built with aiogram 3.x + Telethon, async SQLite, and full two-bot concurrent architecture.

## Features

### Core Functionality

- **Group Catalog**: Paginated list of groups for sale with name and age since creation. Buyers browse, click to open a group, then enter its number to purchase
- **Purchase Flow**: Buyer selects a group — request is stored silently in the database. Admin reviews and approves or rejects. On approval, Telethon automatically adds buyer to the group and grants full admin rights
- **Auto Onboarding**: When a purchase is confirmed, the Telethon account resolves the buyer by username, adds them to the group via MTProto, promotes them to full administrator, and removes the group from its own chat history
- **Gift Flow**: User can transfer ownership of any external group to the Telethon account. Bot detects the transfer via UpdateChannelParticipant event and lists the group for sale automatically
- **Support Bot**: Separate bot instance running concurrently. Live relay chat between buyer and admin — messages pass both ways with inline Reply buttons until user presses Hang Up

### Admin Panel

- Add Telethon accounts step by step: session name, API ID, API Hash, phone, confirmation code, optional 2FA password
- Create groups via Telethon: name, type (open/closed), optional avatar upload, optional description
- Delete groups: removes from Telegram and from database
- Buyer queue: stored silently, shown on demand — confirm or reject each request with inline buttons, processed requests are deleted immediately

### Advanced Features

- **Session Migration**: On first launch, existing sessions from `sessions/` are loaded automatically if a `data.json` is present — no re-authorization needed
- **Already Authorized**: If a session file already exists and is authorized when adding an account — added instantly without requesting a code
- **Device Spoofing**: Each Telethon session gets a random device model, system version, and app version to reduce fingerprinting
- **Concurrent Bots**: Both bots (sales + support) run in one process via `asyncio.gather` sharing the same SQLite database
- **30 Relay Phrases**: Support bot uses 30 unique message relay phrases in Saul Goodman / Jimmy McGill style

## Requirements

- Python 3.10+
- Two Telegram bot tokens (sales bot + support bot)
- At least one Telethon account (API ID + API Hash from my.telegram.org)

## Installation

### 1. Clone the repository

```
git clone https://github.com/yourname/group-resale-bot.git
cd group-resale-bot
```

### 2. Create virtual environment

```
python3 -m venv venv
```

### 3. Activate virtual environment

Linux / macOS:
```
source venv/bin/activate
```

Windows:
```
venv\Scripts\activate
```

### 4. Install dependencies

```
pip install -r requirements.txt
```

### 5. Configure and run

```
cp .env.example .env
nano .env
python main.py
```

On successful start, console output will show:

```
Sales bot polling started
Support bot polling started
Telethon clients loaded
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```
SALES_BOT_TOKEN=your_sales_bot_token_here
SUPPORT_BOT_TOKEN=your_support_bot_token_here
ADMIN_ID=123456789
CARD_NUMBER=4276 1234 5678 9012
SUPPORT_BOT_USERNAME=your_support_bot_username
DB_PATH=data.db
```

**Getting SALES_BOT_TOKEN and SUPPORT_BOT_TOKEN:**
- Message @BotFather on Telegram
- Send `/newbot` twice — create two separate bots
- Copy each token to your `.env`

**Getting ADMIN_ID:**
- Message @userinfobot to get your Telegram user ID
- Only one admin is supported — enter your numeric ID

**CARD_NUMBER:**
- The card number shown to buyers when they confirm a purchase intent
- Displayed inside a copyable `<code>` block in the bot message

**SUPPORT_BOT_USERNAME:**
- Username of your second (support) bot, without the @ symbol
- Used to generate deep links in the sales bot

## Project Structure

```
group-resale-bot/
├── main.py                  # Entry point — starts both bots concurrently
├── config.py                # Environment variable loading
├── database.py              # All database operations (aiosqlite)
├── states.py                # FSM state groups
├── bot_instances.py         # Shared bot references for cross-bot messaging
├── telethon_manager.py      # Telethon auth, group creation, sell_group logic
│
├── handlers/
│   ├── admin.py             # Admin panel — accounts, groups, buyer queue
│   ├── sales.py             # Buyer flow — browse, buy, gift
│   └── support.py           # Support bot — group selection, live chat relay
│
├── keyboards/
│   ├── admin_kb.py          # Admin inline keyboards
│   ├── sales_kb.py          # Buyer inline keyboards
│   └── support_kb.py        # Support inline + reply keyboards
│
├── sessions/                # Telethon .session files (auto-created)
├── requirements.txt
├── .env.example
└── .gitignore
```

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────┐
│                 User Interface                  │
│             (Telegram Messages)                 │
└──────────────┬──────────────────┬───────────────┘
               │                  │
┌──────────────▼──────┐  ┌────────▼──────────────┐
│     Sales Bot       │  │    Support Bot        │
│  ┌───────┬───────┐  │  │  ┌────────┬────────┐  │
│  │ Admin │ Buyer │  │  │  │  User  │ Admin  │  │
│  └───────┴───────┘  │  │  └────────┴────────┘  │
└──────────────┬──────┘  └────────┬───────────────┘
               │                  │
┌──────────────▼──────────────────▼───────────────┐
│                  Data Layer                     │
│  ┌──────────────────┬───────────────────────┐   │
│  │  SQLite Database │   Telethon MTProto     │   │
│  │   (aiosqlite)    │  (group management)   │   │
│  └──────────────────┴───────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 2 Services Running at All Times

| Service | Role |
|---|---|
| Sales bot dispatcher | Admin panel, buyer purchase and gift flow |
| Support bot dispatcher | Live chat relay between buyers and admin |

### Purchase Lifecycle

```
[Buyer presses Buy] → [Paginated group list shown]
                                 │
            [Buyer enters group number]
                                 │
       [Request stored silently in DB]
                                 │
   [Buyer receives card number + wait message]
                                 │
      [Admin presses Buyers button]
                                 │
    [All pending requests shown with buttons]
                                 │
         [Admin presses Confirm]
                                 │
   [Telethon resolves buyer by @username]
                                 │
    [Buyer added to group via MTProto]
                                 │
  [Buyer promoted to full administrator]
                                 │
  [Group removed from account chat history]
                                 │
      [Buyer receives confirmation]
```

### Gift Lifecycle

```
[Buyer presses Gift] → [Bot shows Telethon account @username]
                                 │
   [Buyer transfers group ownership in Telegram]
                                 │
  [Telethon detects UpdateChannelParticipant]
                                 │
      [Group added to catalog automatically]
                                 │
       [Buyer receives thank-you message]
```

### Support Chat Lifecycle

```
[User opens support bot] → [/start]
                                 │
      [Bot shows paginated group catalog]
                                 │
         [User enters group number]
                                 │
   [Admin receives notification with user info]
                                 │
          [User sends question]
                                 │
[Admin sees message + Reply inline button]
                                 │
              [Admin replies]
                                 │
  [User sees reply + Reply inline button]
                                 │
  [Conversation continues both ways...]
                                 │
       [User presses Hang Up button]
                                 │
          [Session closed for both]
```

## User Flow

### First Launch — Sales Bot

```
User: /start
Bot:  Hey! Welcome!

      What would you like to find here?
      [💰 Buy]  [🎁 Gift]  [❓ Ask]
```

### Buying a Group

```
User: [💰 Buy]
Bot:  Here are our groups:

      1. My Cool Group (2д 5ч)
      2. Another Group (14д 3ч)
      3. Fresh Group (0ч 45м)

      Enter the number of the group you want to buy:

User: 2
Bot:  🔥 Looks like you're serious!

      Pay to this card number: 4276 1234 5678 9012

      ⏳ Waiting for confirmation...

[Admin presses Buyers]

Bot → Admin:
      🆕 New request

      👤 Name: John Doe
      🆔 ID: 123456789
      📎 Username: @johndoe

      📦 Group: Another Group (14д 3ч)
      🔗 Link: https://t.me/+xxxxx
      📅 Request: 14.03.2026 17:42

      [✅ Confirm]  [❌ Reject]

Admin: [✅ Confirm]
Bot → Buyer: 🎉 You lucky one — the group is yours!
             You have been added and granted admin rights. Good luck 🚀
```

### Gifting a Group

```
User: [🎁 Gift]
Bot:  You want to give me a group as a gift?

      Thank you, friend! Please transfer the group to my computer:
      @telethon_account_username

      Once you do — I'll feel it right away! 😊

[User transfers group ownership in Telegram]

Bot → User: 💖 From the bottom of my heart — respect!

            Group «Group Name» accepted and listed for sale.
            Thank you friend — you really helped me! 🙏
```

### First Launch — Support Bot

```
User: /start
Bot:  Welcome! We've met before, haven't we?
      Yes, yes — in my brother's place! Well, glad to see you again! 😊

      Which channel are you interested in?

      1. My Cool Group (2д 5ч)
      2. Another Group (14д 3ч)
      [➡️]

User: 1
Bot:  Got it!

      Write to my boss — he'll give you an answer.
      When you're done, press the button below 👇
      [📵 Hang Up]

User: Hello, I have a question about this group...
Bot:  📡 Transmitting to the boss...

Bot → Admin:
      💬 Message from John Doe (@johndoe, ID: 123456789):

      Hello, I have a question about this group...
      [↩️ Reply]

Admin: [↩️ Reply]
Bot:  ✏️ Enter reply for user 123456789:

Admin: Sure, what would you like to know?

Bot → User: 📩 Reply from boss:

            Sure, what would you like to know?
            [↩️ Reply]

User: [📵 Hang Up]
Bot:  📵 I think you had a great conversation!

      Well, say hi to my brother. Bye! 👋
```

## Admin Panel

Access by sending `/start` as the admin user.

### Main Menu

```
Admin: /start
Bot:   👑 Admin panel

       [➕ Add Telethon Account]
       [📁 Create Group]
       [🗑 Delete Group]
       [👥 Buyers]
```

### Adding Telethon Account

```
Admin: [➕ Add Telethon Account]
Bot:   Enter session name (example: account1):

Admin: account1
Bot:   Enter API ID from my.telegram.org:

Admin: 12345678
Bot:   Enter API Hash:

Admin: abc123def456...
Bot:   Enter phone number (+79991234567):

Admin: +79991234567
Bot:   ✅ Code sent to +79991234567

       Enter the code (spaces allowed: 1 2 3 4 5):

Admin: 1 2 3 4 5
Bot:   ✅ Account @username successfully added!
```

> How to get API ID and API Hash: Go to my.telegram.org, log in with the Telethon account's phone number, go to API development tools → Create application, fill in any app name, save the API ID and API Hash.

### Creating a Group

```
Admin: [📁 Create Group]
Bot:   Enter group name:

Admin: My New Group
Bot:   Group type:
       [🔓 Open]  [🔒 Closed]

Admin: [🔓 Open]
Bot:   Do you need an avatar?
       [✅ Yes]  [❌ No]

Admin: [✅ Yes]
Bot:   Send a photo for the avatar:

Admin: [sends photo]
Bot:   Enter description or skip:
       [➡️ Skip]

Admin: [➡️ Skip]
Bot:   ✅ Group created!

       📌 Name: My New Group
       🔗 Link: https://t.me/+xxxxx
       🔓 Type: Open
       🖼 Avatar: ✅ Yes
       📄 Description: None
       🕐 Created: 14.03.2026 18:00
       👤 Account: @account1
```

### Buyer Queue

```
Admin: [👥 Buyers]
Bot:   👥 Purchase requests (2 pcs.):

       🆕 New request

       👤 Name: John Doe
       🆔 ID: 123456789
       📎 Username: @johndoe

       📦 Group: My Cool Group (2д 5ч)
       🔗 Link: https://t.me/+xxxxx
       📅 Request: 14.03.2026 17:42

       [✅ Confirm]  [❌ Reject]
```

## Deployment (VPS — Recommended)

```
# 1. Connect to your server
ssh user@your-server-ip

# 2. Clone and setup
git clone https://github.com/yourname/group-resale-bot.git
cd group-resale-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
nano .env

# 4. Test run
python main.py

# 5. Create systemd service
sudo nano /etc/systemd/system/resalebot.service
```

Paste this content:

```
[Unit]
Description=Group Resale Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/group-resale-bot
Environment=PATH=/home/yourusername/group-resale-bot/venv/bin
ExecStart=/home/yourusername/group-resale-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```
# Enable and start
sudo systemctl enable resalebot
sudo systemctl start resalebot
sudo systemctl status resalebot

# View live logs
journalctl -u resalebot -f
```

## Troubleshooting

**Bot not adding buyer to group after confirmation**

- Verify the Telethon account is still authorized — check `sessions/` for valid `.session` files
- Buyer must have a public `@username` set in Telegram for the primary resolution method to work
- Check that the Telethon account is a member (or creator) of the target group
- Restart the bot — on startup it reloads all sessions from database

**Telethon sessions not loading after restart**

- If you had sessions in `sessions/` folder and a `data.json` from a previous project, the bot migrates them automatically on first launch
- Check that `API_ID` and `API_HASH` stored in the database match the session file
- If a session is corrupt, delete the `.session` file and re-add the account via admin panel

**"Message is not modified" error**

- Already handled — all `edit_text` calls are wrapped with `TelegramBadRequest` catching
- If you see it in logs it means double-tap on a button — safe to ignore

**Support bot not relaying messages**

- Verify `SUPPORT_BOT_USERNAME` in `.env` matches the actual bot username exactly (without @)
- Both bots must be running — they start together via `asyncio.gather` in `main.py`
- Make sure `ADMIN_ID` is correct — relay messages go to this ID on the support bot

**Database locked**

- Only one instance of the bot should be running at a time
- Stop all running instances before restarting
- Check with `ps aux | grep python`

**Bot not responding after restart**

- Check that all environment variables in `.env` are set correctly
- Run `python main.py` directly in terminal to see startup errors

## Dependencies

```
aiogram==3.7.0       # Async Telegram Bot framework
telethon==1.34.0     # MTProto client for Telethon worker accounts
aiosqlite==0.20.0    # Async SQLite database
python-dotenv==1.0.1 # .env file support
```

## Security

- Never commit `.env` or `sessions/` to Git — already in `.gitignore`
- Admin ID is verified on every single admin command — no privilege escalation possible
- Telethon `.session` files provide full account access — treat them like passwords and never share them
- Card number is stored only in `.env`, never in the database

## Performance

| Metric | Value |
|---|---|
| Database | SQLite (suitable for up to ~100K users) |
| Memory usage | ~30–60MB typical |
| Concurrent bots | 2 (single process, asyncio.gather) |
| Buyer onboarding | automatic, within seconds of admin approval |
| Session loading | automatic on startup from database |

For large user bases (50K+), consider migrating to PostgreSQL by replacing aiosqlite with asyncpg.

## Issues & Support

- Bug reports and feature requests: open an issue on GitHub

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

See LICENSE file for full text.

What this means:

- Free to use commercially
- Can modify and distribute
- Must disclose source code
- Must use the same license
- Must state changes made

---

Made with ❤️ for the Telegram community

Star this repo if you find it useful! ⭐