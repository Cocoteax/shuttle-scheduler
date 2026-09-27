# 🏸 Shuttle Scheduler

Shuttle Scheduler is a Python command-line application for scheduling Telegram messages using a **Telegram user account** rather than a Telegram bot.

It was created primarily to make it easier to schedule recurring badminton game announcements across Telegram chats, groups, and forum topics without manually creating every scheduled message through the Telegram app.

Shuttle Scheduler supports scheduling the **same message across multiple Telegram destinations at once**, including normal groups and specific topics inside Telegram Forum groups.

The application uses [Telethon](https://github.com/LonamiWebs/Telethon) to communicate with Telegram and uses **Telegram's server-side scheduling**. Once messages have been scheduled successfully, Shuttle Scheduler disconnects and exits. Your computer does not need to remain running until the messages are delivered.

---

## Features

### Supported Telegram destinations

Shuttle Scheduler supports:

- Saved Messages
- Private chats
- Regular Telegram groups
- Telegram supergroups
- Forum/topic-enabled Telegram groups
- Individual topics within forum groups
- Multiple destinations in a single scheduling operation
- Mixed destination types through the All Available Chats interface

Chats, groups, and forum topics are discovered dynamically from the authenticated Telegram account rather than being hard-coded.

---

## Multi-Destination Scheduling

Shuttle Scheduler can schedule the same message across **multiple Telegram destinations in one operation**.

For example:

```text
GROUPS

[1] Saturday Badminton
[2] SG Badminton Kakis
[3] Badminton Community [Forum]
[4] Tampines Badminton
[5] Bedok Games

Select one or more:
> 1,3,4
```

Comma-separated selections allow multiple destinations to be selected at once.

The same message and scheduling configuration are then applied across all selected destinations.

### Mixed destination types

The **All Available Chats** interface can also be used to combine different destination types.

For example:

```text
[1] Alice [Private]
[2] Saturday Badminton [Group]
[3] Badminton Community [Forum]
[4] Bob [Private]

Select one or more:
> 1,2,3
```

This allows one scheduling operation to target, for example:

```text
✓ Alice
✓ Saturday Badminton
✓ Badminton Community → East Games
```

---

## Telegram Forum Topics

Shuttle Scheduler automatically detects when a selected Telegram group is configured as a **Forum/Topics group**.

For a normal group:

```text
Select Group
    ↓
Enter Message
    ↓
Configure Schedule
```

For a forum-enabled group:

```text
Select Forum Group
    ↓
Select Topic
    ↓
Enter Message
    ↓
Configure Schedule
```

For example:

```text
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

The topic list is retrieved from Telegram.

A forum topic is resolved as a combination of its **parent group** and **specific topic** so that scheduled messages are delivered into the intended conversation thread.

When multiple destinations are selected, each selected Forum group is resolved to its chosen topic before scheduling continues.

For example:

```text
SELECTED DESTINATIONS

[1] Saturday Badminton
    Type: Group

[2] Badminton Community → East Games
    Type: Forum topic

[3] Tampines Badminton
    Type: Group

Total destinations: 3
```

---

## Custom Messages

Messages are entered directly through the command-line interface.

Multiline messages, blank lines, Unicode characters, and emojis are supported.

For example:

```text
🏸 BADMINTON GAME

📅 Saturday
⏰ 8:00 PM - 10:00 PM
📍 Sports Hall

Intermediate+

PM me to join!
```

When multiple destinations are selected, the message only needs to be entered **once**.

The same message is then scheduled across every selected destination.

---

## Scheduling Modes

Shuttle Scheduler supports two scheduling modes.

### 1. Single Scheduled Message

Schedule one message for a specific future date and time.

For multiple destinations:

```text
3 destinations
×
1 scheduled time
=
3 Telegram scheduled messages
```

### 2. Interval Scheduling

Schedule the same message multiple times per day across multiple consecutive days.

You can configure:

- Start date
- Daily start time
- Daily end time
- Interval between messages
- Number of consecutive days

Decimal-hour intervals are supported:

```text
0.5  = 30 minutes
1    = 1 hour
1.5  = 1 hour 30 minutes
2    = 2 hours
2.25 = 2 hours 15 minutes
```

For example:

```text
Start date:       15/09/2026
Daily start:      09:00
Daily end:        14:00
Interval:         1.5 hours
Number of days:   2
```

generates:

```text
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

The daily interval resets at the configured start time on each new day rather than continuing overnight.

When multiple destinations are selected, the schedule is generated once and applied to every destination.

For example:

```text
3 destinations
×
8 scheduled times
=
24 Telegram scheduled messages
```

Each resulting message is submitted individually to Telegram's server-side scheduler.

---

## Schedule Preview and Confirmation

**Nothing is scheduled until you explicitly confirm it.**

Before submission, Shuttle Scheduler displays:

- Every selected destination
- Destination type
- Selected Forum topics
- Message contents
- Scheduling interval
- Daily scheduling window
- Number of days
- Generated timestamps
- Number of destinations
- Number of scheduled timestamps
- Total number of Telegram messages

For example:

```text
========================================
FINAL SCHEDULE PREVIEW
========================================

DESTINATIONS

[1] Saturday Badminton
    Type: Group

[2] Badminton Community → East Games
    Type: Forum topic

[3] Tampines Badminton
    Type: Group

----------------------------------------

MESSAGE

🏸 Badminton game available!

Tuesday 8-10 PM
PM me to join.

----------------------------------------

SCHEDULE

Daily window:
09:00 - 20:00

Interval:
Every 1.5 hours

Days:
2

----------------------------------------

Destinations:
3

Scheduled timestamps:
16

TOTAL TELEGRAM MESSAGES:
48

========================================

You are about to schedule 48 Telegram messages
across 3 destinations.

Proceed? (y/n):
>
```

Only explicit confirmation causes the scheduling operation to begin.

---

## Batch Safety

Multi-destination interval scheduling can generate a large number of messages very quickly.

Shuttle Scheduler therefore calculates:

```text
number of destinations
×
number of scheduled timestamps
=
total Telegram messages
```

before anything is submitted.

The current application also uses a safety limit of:

```text
100 messages per operation
```

If a configuration would exceed this limit, the operation is rejected before submission.

This is an **application safety limit**, not a statement about Telegram's own API limits.

---

## Submission Results

For multi-destination operations, Shuttle Scheduler reports both overall and per-destination results.

For example:

```text
========================================
SCHEDULING COMPLETE
========================================

OVERALL

Successfully scheduled: 47
Failed: 1
Total attempted: 48

----------------------------------------

BY DESTINATION

Saturday Badminton
  Successful: 16
  Failed: 0

Badminton Community → East Games
  Successful: 15
  Failed: 1

Tampines Badminton
  Successful: 16
  Failed: 0
```

A failed individual request is not reported as successful.

---

## Server-Side Scheduling

Shuttle Scheduler does **not** need to remain running until each message needs to be sent.

The workflow is:

```text
Select destinations
        ↓
Resolve Forum topics
        ↓
Enter message
        ↓
Configure schedule
        ↓
Generate timestamps
        ↓
Preview complete operation
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

- A continuously running Python process
- A cloud server
- A background worker
- Cron for already-submitted messages
- Keeping VS Code open

Once Telegram accepts the scheduled messages, Telegram handles their future delivery.

---

# 🚀 Getting Started

This section contains everything needed to install and run Shuttle Scheduler from a fresh copy of the repository.

## 1. Prerequisites

You need:

- A Telegram account
- Python 3
- Git
- A Telegram API ID and API Hash

Shuttle Scheduler uses:

- `Telethon`
- `python-dotenv`

These Python dependencies are installed automatically from `requirements.txt`.

### Check Python

On macOS or Linux:

```bash
python3 --version
```

On Windows:

```powershell
python --version
```

If Python is not installed on macOS and you use Homebrew:

```bash
brew install python
```

---

## 2. Clone the Repository

Open Terminal and run:

```bash
git clone <YOUR-REPOSITORY-URL>
cd shuttle-scheduler
```

Replace `<YOUR-REPOSITORY-URL>` with the URL of this GitHub repository.

---

## 3. Create a Python Virtual Environment

Using a virtual environment keeps Shuttle Scheduler's Python packages separate from the rest of your computer.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

After activation, your terminal will normally show something similar to:

```text
(.venv)
```

---

## 4. Install Dependencies

With the virtual environment activated:

```bash
python -m pip install -r requirements.txt
```

This installs the Python packages required by Shuttle Scheduler.

---

## 5. Obtain Telegram API Credentials

Shuttle Scheduler connects through your **Telegram user account**, not a Telegram bot.

Go to:

https://my.telegram.org/

Sign in with the Telegram account you want Shuttle Scheduler to use.

Open:

**API development tools**

Create an application if you do not already have one.

Telegram will provide:

```text
App api_id
App api_hash
```

Treat these values as credentials.

Do not post them publicly or commit them to GitHub.

---

## 6. Create the `.env` File

In the root of the Shuttle Scheduler project, create:

```text
.env
```

Add:

```text
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

Replace the placeholder values with your actual Telegram API credentials.

For example, your project should now look approximately like:

```text
shuttle-scheduler/
├── .env
├── .gitignore
├── .venv/
├── README.md
├── requirements.txt
└── scheduler.py
```

The `.env` file is deliberately excluded from Git.

---

## 7. Start Shuttle Scheduler

Make sure the virtual environment is active.

### macOS / Linux

```bash
source .venv/bin/activate
python scheduler.py
```

### Windows

```powershell
.venv\Scripts\activate
python scheduler.py
```

---

## 8. Authenticate With Telegram — First Run Only

On the first run, Telethon may ask for:

- Your Telegram phone number
- A Telegram login verification code
- Your Two-Step Verification password, if enabled

Enter these directly into your local terminal.

Do **not** share your verification code or Two-Step Verification password.

After successful authentication, Telethon creates a local session file, typically:

```text
shuttle_scheduler.session
```

This allows Shuttle Scheduler to authenticate on later runs without requesting a new Telegram login code every time.

The authorized session may also appear under:

**Telegram → Settings → Devices**

This is expected.

Do not terminate that Telegram session unless you intentionally want to revoke Shuttle Scheduler's authorization.

---

## 9. Use Shuttle Scheduler

After authentication, the application displays its interactive interface:

```text
What would you like to schedule to?

[1] Saved Messages
[2] Private chats
[3] Groups
[4] All available chats
[Q] Quit
```

From here:

1. Select one or more destinations.
2. If a selected group uses Telegram Forum Topics, select the required topic.
3. Review the resolved destination list.
4. Enter your message.
5. Choose **Single** or **Interval** scheduling.
6. Configure the date/time or interval schedule.
7. Review the complete final preview.
8. Check the destination count and total Telegram message count carefully.
9. Confirm the operation.

After Telegram accepts the scheduled messages, Shuttle Scheduler disconnects and displays:

```text
Session disconnected.
```

The Python process then exits.

Telegram's servers handle future message delivery.

### Running Shuttle Scheduler Again

You do not need to repeat the installation steps every time.

Open Terminal, navigate to the project:

```bash
cd /path/to/shuttle-scheduler
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Then run:

```bash
python scheduler.py
```

That's all that's required for normal day-to-day use.

---

## ⚠️ Security

The following files contain sensitive information and must **never** be committed, uploaded, or shared:

```text
.env
*.session
*.session-journal
```

The `.env` file contains your Telegram API credentials.

The Telethon `.session` file represents an authenticated Telegram session and should be treated like a credential.

Your Python virtual environment should also remain local:

```text
.venv/
```

A suitable `.gitignore` includes:

```gitignore
.env
.venv/
*.session
*.session-journal
__pycache__/
*.pyc
.DS_Store
```

Before pushing changes to GitHub, you can verify everything Git is tracking with:

```bash
git ls-files
```

Make sure `.env`, `.venv/`, and all `.session` files are absent.

---

## Time Zone

The current application uses:

```text
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

Current working functionality:

- [x] Telegram user authentication
- [x] Persistent local Telethon session
- [x] Saved Messages
- [x] Private chat discovery and selection
- [x] Regular Telegram groups
- [x] Telegram supergroups
- [x] Forum/topic group detection
- [x] Forum topic discovery
- [x] Individual forum topic selection
- [x] Scheduled messages to forum topics
- [x] Multiline custom messages
- [x] Single scheduled messages
- [x] Interval scheduling
- [x] Configurable daily scheduling window
- [x] Decimal-hour intervals
- [x] Multiple consecutive scheduling days
- [x] Past-time exclusion
- [x] Multiple destination selection
- [x] Multiple group selection
- [x] Mixed private/group destination selection
- [x] Forum topics within multi-destination operations
- [x] Destination review before scheduling
- [x] Total batch message calculation
- [x] Batch safety limit
- [x] Complete schedule preview
- [x] Explicit confirmation
- [x] Telegram server-side scheduling
- [x] Overall submission result reporting
- [x] Per-destination result reporting
- [x] Explicit session disconnection

---

## Current Scheduling Model

A scheduling operation currently uses:

```text
ONE message
+
ONE scheduling configuration
+
ONE OR MORE destinations
```

For example:

```text
Message:
🏸 Tuesday Game
8-10 PM
PM me to join

Destinations:
✓ Saturday Badminton
✓ Tampines Badminton
✓ Badminton Community → East Games

Schedule:
09:00
10:30
12:00
13:30
```

This produces:

```text
3 destinations
×
4 timestamps
=
12 Telegram scheduled messages
```

This model keeps the workflow fast for hosts who want to advertise the same game across several Telegram communities.

---

## License

No license has been specified yet.