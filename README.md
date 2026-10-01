# 🏸 Shuttle Scheduler

> **NOTE:** This README supersedes the previous version and includes the latest features:
>
> - Multi-destination scheduling
> - Telegram Forum Topic support
> - Bulk updating of future scheduled messages within selected destinations
> - Message variant detection before bulk updates

## Overview

Shuttle Scheduler is a Python command-line application for scheduling Telegram messages using your **Telegram user account** (via Telethon), rather than a Telegram bot.

It was created primarily to automate recurring badminton advertisements across multiple Telegram groups and forum topics without manually creating every scheduled message through the Telegram app.

Unlike a traditional scheduler, Shuttle Scheduler submits **Telegram server-side scheduled messages**. Once scheduling has completed successfully, the application disconnects and exits. Your computer does **not** need to remain running until the scheduled messages are delivered.

---

# Core Features

- Saved Messages
- Private chats
- Regular Telegram groups
- Supergroups
- Forum / Topic-enabled groups
- Individual Forum Topic selection
- Multi-destination scheduling
- Single scheduling
- Interval scheduling
- Bulk updating of future scheduled messages
- Destination-scoped updates
- Scheduled-message variant detection
- Telegram server-side scheduling

---

# Multi-Destination Scheduling

The same message can be scheduled across multiple Telegram destinations in one operation.

Example:

```text
GROUPS

[1] Saturday Badminton
[2] SG Badminton Kakis
[3] Badminton Community [Forum]
[4] Tampines Badminton

Select one or more:
> 1,3,4
```

Forum groups automatically prompt for Topic selection before continuing.

The scheduling configuration is entered once and applied to every selected destination.

---

# Update Future Scheduled Messages

Future scheduled messages can be updated in bulk without affecting already-delivered messages.

Workflow:

```text
Select destinations
        ↓
Resolve Forum Topics
        ↓
Retrieve future scheduled messages
        ↓
Group by identical message content
        ↓
Display message variants
        ↓
Update ALL / Cancel
        ↓
Enter replacement message
        ↓
Final confirmation
        ↓
Edit future scheduled messages
```

Only the selected destinations are searched.

Messages in unselected chats, groups and topics remain untouched.

If multiple different message bodies exist, Shuttle Scheduler displays each unique variant together with the destinations currently using it before asking whether to update everything.

---

# Server-side Scheduling

```text
Select destinations
        ↓
Resolve Forum Topics
        ↓
Enter message
        ↓
Configure schedule
        ↓
Preview
        ↓
Confirm
        ↓
Submit to Telegram
        ↓
Disconnect
        ↓
Python exits
        ↓
Telegram delivers later
```

---

# 🚀 Getting Started

## 1. Prerequisites

You need:

- A Telegram account
- Python 3
- Git
- A Telegram API ID and API Hash

Python dependencies:

- Telethon
- python-dotenv

### Check Python

macOS / Linux

```bash
python3 --version
```

Windows

```powershell
python --version
```

If Python is not installed on macOS and you use Homebrew:

```bash
brew install python
```

---

## 2. Clone the Repository

```bash
git clone <YOUR-REPOSITORY-URL>
cd shuttle-scheduler
```

---

## 3. Create a Virtual Environment

macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 4. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

## 5. Obtain Telegram API Credentials

Visit:

https://my.telegram.org/

Create an application under **API development tools**.

Telegram provides:

```text
App api_id
App api_hash
```

---

## 6. Create `.env`

```text
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

---

## 7. Start Shuttle Scheduler

macOS / Linux

```bash
source .venv/bin/activate
python scheduler.py
```

Windows

```powershell
.venv\Scripts\activate
python scheduler.py
```

---

## 8. First Authentication

On first launch Telethon may ask for:

- Phone number
- Telegram login code
- Two-Step Verification password (if enabled)

A local session file (`shuttle_scheduler.session`) will then be created.

Future runs reuse this session.

---

## 9. Daily Usage

Launch:

```bash
source .venv/bin/activate
python scheduler.py
```

Choose:

- Schedule new messages
- Update future scheduled messages

Follow the prompts.

When complete, the application disconnects and prints:

```text
Session disconnected.
```

Telegram will deliver the scheduled messages later.

---

# Security

Never commit:

```text
.env
*.session
*.session-journal
.venv/
```

Always verify tracked files:

```bash
git ls-files
```

---

# Project Status

- [x] Telegram authentication
- [x] Multi-destination scheduling
- [x] Forum Topic support
- [x] Interval scheduling
- [x] Bulk updating of future scheduled messages
- [x] Destination-scoped updates
- [x] Variant detection
- [x] Batch safety limits
- [x] Explicit confirmation
- [x] Session disconnection

---

# License

No license has been specified yet.
