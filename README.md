# 🏸 Shuttle Scheduler

Shuttle Scheduler is a Python command-line application for scheduling Telegram messages using a **Telegram user account** rather than a Telegram bot.

It was created primarily to make it easier to schedule recurring badminton game announcements across Telegram chats, groups, and forum topics without manually creating every scheduled message through the Telegram app.

The application uses [Telethon](https://github.com/LonamiWebs/Telethon) to communicate with Telegram and uses **Telegram's server-side scheduling**. Once messages have been scheduled successfully, Shuttle Scheduler disconnects and exits. The computer does not need to remain running until the messages are delivered.

---

## Features

### Supported Telegram destinations

Shuttle Scheduler currently supports:

* Saved Messages
* Private chats
* Regular Telegram groups
* Telegram supergroups
* Forum/topic-enabled Telegram groups
* Individual topics within forum groups
* Interactive discovery of chats available to the authenticated Telegram account

Private chats, groups, and forum topics use the same core scheduling functionality.

### Interactive destination selection

Run the application from a terminal and select where the message should be scheduled.

```text id="as9rqh"
What would you like to schedule to?

[1] Saved Messages
[2] Private chats
[3] Groups
[4] All available chats
[Q] Quit
```

Chats and groups are retrieved dynamically from Telegram rather than being hard-coded.

### Telegram Forum Topics

Shuttle Scheduler detects when a selected Telegram group is configured as a **Forum/Topics group**.

For a regular group:

```text id="pl96dg"
Select Group
    ↓
Enter Message
    ↓
Configure Schedule
```

For a forum-enabled group:

```text id="a65c4j"
Select Forum Group
    ↓
Select Topic
    ↓
Enter Message
    ↓
Configure Schedule
```

For example:

```text id="iqfwxg"
========================================
SELECT TOPIC
========================================

Group:
Badminton Community

[1] General
[2] North Games
[3] East Games
[4] West Games

[B] Back
[Q] Quit

Select topic:
>
```

The actual topics are retrieved from Telegram.

Messages scheduled to a topic retain both the **parent group** and the **selected topic**, ensuring that Telegram delivers the message into the intended conversation thread.

Forum topics support the same Single and Interval scheduling modes as normal groups and private chats.

---

## Custom Messages

Messages are entered directly through the command-line interface.

Multiline messages, blank lines, Unicode characters, and emojis are supported.

For example:

```text id="a6hm80"
🏸 BADMINTON GAME

📅 Saturday
⏰ 8:00 PM - 10:00 PM
📍 Sports Hall

Intermediate+

PM me to join!
```

Message content does not need to be hard-coded into the application.

---

## Scheduling Modes

Shuttle Scheduler supports two scheduling modes.

### 1. Single Scheduled Message

Schedule one message for a specific future date and time.

The application displays a complete preview and requires explicit confirmation before submitting the scheduled message to Telegram.

### 2. Interval Scheduling

Schedule the same message multiple times per day across multiple consecutive days.

The user can configure:

* Start date
* Daily start time
* Daily end time
* Interval between messages
* Number of consecutive days

Decimal-hour intervals are supported.

Examples:

```text id="02d51n"
0.5  = 30 minutes
1    = 1 hour
1.5  = 1 hour 30 minutes
2    = 2 hours
2.25 = 2 hours 15 minutes
```

For example:

```text id="0sp8xj"
Start date:       15/09/2026
Daily start:      09:00
Daily end:        14:00
Interval:         1.5 hours
Number of days:   2
```

generates:

```text id="i8qu15"
15/09/2026
09:00
10:30
12:00
13:30

16/09/2026
09:00
10:30
12:00
13:30
```

Each generated timestamp is submitted to Telegram as an individual server-side scheduled message.

The daily interval resets at the configured start time on each new day rather than continuing overnight.

---

## Schedule Preview and Confirmation

Nothing is scheduled until the user explicitly confirms it.

Before submission, Shuttle Scheduler displays information including:

* Destination
* Destination type
* Message
* Scheduling interval
* Daily scheduling window
* Number of days
* Generated timestamps
* Total number of messages

For a forum topic, both the group and topic are shown:

```text id="rzs8cy"
========================================
SCHEDULE PREVIEW
========================================

Destination type:
Forum topic

Group:
Badminton Community

Topic:
East Games

Message:
----------------------------------------
🏸 Badminton game available!
PM me if interested.
----------------------------------------

Interval:
Every 1.5 hours

Daily window:
09:00 - 20:00

Days:
2

Generated schedule:
...

Total messages:
16
```

The user must explicitly confirm before anything is submitted to Telegram.

---

## Server-Side Scheduling

Shuttle Scheduler does **not** need to remain running until each message needs to be sent.

The workflow is:

```text id="l3hzy7"
Configure schedule
        ↓
Generate schedule
        ↓
Preview
        ↓
Confirm
        ↓
Submit scheduled messages to Telegram
        ↓
Disconnect
        ↓
Python exits
        ↓
Telegram delivers messages later
```

There is no need for:

* A continuously running Python process
* A cloud server
* A background worker
* Cron for already-submitted messages
* Keeping VS Code open

Once Telegram has successfully accepted the scheduled messages, Telegram handles their future delivery.

---

## Destination Architecture

The application resolves the selected Telegram destination before entering the common scheduling workflow.

```text id="9eqzup"
                 Destination
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
 Saved Messages    Private       Group
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                    Normal Group      Forum Group
                                           │
                                           ▼
                                      Select Topic
                                           │
       ┌───────────────────────────────────┘
       ▼
 Resolved Destination
       │
       ▼
 Shared Scheduler
       │
 ┌─────┴─────┐
 ▼           ▼
Single    Interval
 │           │
 └─────┬─────┘
       ▼
    Preview
       ▼
    Confirm
       ▼
Telegram Server-Side Scheduling
       ▼
  Disconnect
```

This allows Private Chats, Groups, and Forum Topics to share the same core scheduling engine.

---

## Current Limitation

Shuttle Scheduler currently supports **one destination per scheduling operation**.

For example, you can select:

```text id="g8ex54"
Private Chat
```

or:

```text id="kbfr3e"
Badminton Group
```

or:

```text id="f1lrlj"
Badminton Community
→ East Games
```

and schedule one or many future messages for that destination.

Selecting multiple destinations in a single operation is **not yet supported**.

---

## Requirements

* Python 3
* Telegram account
* Telegram API ID and API Hash
* Telethon
* python-dotenv

The project uses Python's built-in `venv` for dependency isolation.

---

## Installation

Clone the repository:

```bash id="egk4r8"
git clone <YOUR-REPOSITORY-URL>
cd shuttle-scheduler
```

Create a virtual environment.

### macOS / Linux

```bash id="xf7q9j"
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell id="ak5kh8"
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash id="l82teq"
pip install -r requirements.txt
```

---

## Telegram API Credentials

Shuttle Scheduler requires Telegram API credentials for your own Telegram account.

Create a Telegram application through:

https://my.telegram.org/

Then create a local `.env` file in the project directory:

```text id="xx7fnq"
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

Never commit this file to Git.

---

## First Authentication

The first time the application authenticates with Telegram, Telethon may request:

* Your Telegram phone number
* Telegram login verification code
* Two-Step Verification password, if enabled

After successful authentication, Telethon creates a local session file, typically:

```text id="ilrswt"
shuttle_scheduler.session
```

This allows subsequent runs to authenticate without requesting a new verification code each time.

The authorized Telethon session may also appear under **Telegram → Settings → Devices**.

---

## ⚠️ Security

The following files contain sensitive information and must never be committed, uploaded, or shared:

```text id="t4mxnf"
.env
*.session
*.session-journal
```

The `.env` file contains Telegram API credentials.

The Telethon `.session` file represents an authenticated Telegram session and should be treated as a credential.

The Python virtual environment should also remain local:

```text id="wev9nu"
.venv/
```

A suitable `.gitignore` includes:

```gitignore id="6z1qxf"
.env
.venv/
*.session
*.session-journal
__pycache__/
*.pyc
.DS_Store
```

Before pushing changes, check what Git is actually tracking:

```bash id="0k9flm"
git ls-files
```

Make sure `.env`, `.venv/`, and all `.session` files are absent.

---

## Usage

Activate the virtual environment.

### macOS / Linux

```bash id="g93x1x"
source .venv/bin/activate
```

### Windows

```powershell id="0z0dtz"
.venv\Scripts\activate
```

Start Shuttle Scheduler:

```bash id="wdt8y5"
python scheduler.py
```

Follow the interactive prompts to:

1. Select a Telegram destination.
2. Select a topic if the destination is a forum-enabled group.
3. Enter the message.
4. Choose Single or Interval scheduling.
5. Configure the schedule.
6. Review the generated schedule.
7. Confirm submission.

After the scheduled messages have been submitted, the application disconnects from Telegram and displays:

```text id="dvlgjq"
Session disconnected.
```

The Python process then exits while Telegram handles future delivery.

---

## Time Zone

The current application uses:

```text id="bgb1xy"
Asia/Singapore
```

for scheduling and schedule previews.

---

## Responsible Use

Shuttle Scheduler operates through an authenticated Telegram **user account**, not a Telegram bot.

It should only be used in chats, groups, and topics where the authenticated account is normally permitted to post.

The application does not attempt to bypass Telegram permissions or group restrictions.

Automated or high-volume messaging may be subject to Telegram limits and policies. Use reasonable scheduling frequencies and comply with Telegram's Terms of Service and the rules of the groups in which you participate.

---

## Project Status

Current working and tested functionality:

* [x] Telegram user authentication
* [x] Persistent local Telethon session
* [x] Saved Messages
* [x] Private chat discovery and selection
* [x] Regular Telegram groups
* [x] Telegram supergroups
* [x] Forum/topic group detection
* [x] Forum topic discovery
* [x] Individual forum topic selection
* [x] Scheduled messages to forum topics
* [x] Multiline custom messages
* [x] Single scheduled messages
* [x] Interval scheduling
* [x] Configurable daily scheduling window
* [x] Decimal-hour intervals
* [x] Multiple consecutive scheduling days
* [x] Past-time exclusion
* [x] Schedule preview
* [x] Explicit confirmation
* [x] Telegram server-side scheduling
* [x] Submission success/failure reporting
* [x] Explicit session disconnection
* [ ] Multiple destinations in one scheduling operation

---

## Planned Next Step

The next major feature is **multi-destination scheduling**.

The goal is to select multiple Telegram destinations and apply one message and scheduling configuration across them.

For example:

```text id="13zvpo"
GROUPS

[1] Saturday Badminton
[2] SG Badminton Kakis
[3] Badminton Community [Forum]
[4] Tampines Badminton

Select one or more:
> 1,3,4
```

For forum-enabled groups, the interface will need to preserve specific topic selection so the final destinations might conceptually be:

```text id="yj2al5"
✓ Saturday Badminton
✓ Badminton Community → East Games
✓ Tampines Badminton
```

Before submission, Shuttle Scheduler should calculate the complete operation:

```text id="us5qmw"
3 destinations
×
8 scheduled times
=
24 Telegram scheduled messages
```

and show the complete destination list, generated schedule, and total number of Telegram messages before requiring explicit confirmation.

---

## License

No license has been specified yet.
