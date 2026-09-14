# 🏸 Shuttle Scheduler

Shuttle Scheduler is a Python command-line application for scheduling Telegram messages using a **Telegram user account** rather than a Telegram bot.

It was created primarily to make it easier to schedule recurring badminton game announcements in Telegram groups without manually creating every scheduled message through the Telegram app.

The application uses [Telethon](https://github.com/LonamiWebs/Telethon) to communicate with Telegram and submits messages using **Telegram's server-side scheduling**. Once the messages have been scheduled successfully, Shuttle Scheduler can disconnect and exit. The computer does not need to remain running until the messages are delivered.

## Features

### Telegram destinations

Shuttle Scheduler currently supports:

* Saved Messages
* Private chats
* Telegram groups
* Interactive discovery of chats available to the authenticated Telegram account

Private chats and groups use the same scheduling functionality.

### Interactive command-line interface

Run the application from a terminal and select the destination interactively.

Example:

```text
What would you like to schedule to?

[1] Saved Messages
[2] Private chats
[3] Groups
[4] All available chats
[Q] Quit
```

Chats and groups are retrieved dynamically from Telegram rather than being hard-coded into the application.

### Custom messages

Messages are entered directly through the command-line interface.

Multiline messages and Unicode characters such as emojis are supported.

For example:

```text
🏸 BADMINTON GAME

📅 Saturday
⏰ 8:00 PM - 10:00 PM
📍 Sports Hall

PM me to join!
```

### Single scheduled messages

A message can be scheduled for a specific future date and time.

The application displays a preview and requires confirmation before submitting the scheduled message to Telegram.

### Interval scheduling

The same message can be scheduled multiple times per day over multiple consecutive days.

The user can configure:

* Start date
* Daily start time
* Daily end time
* Interval between messages
* Number of consecutive days

Decimal-hour intervals are supported.

Examples:

```text
0.5  = 30 minutes
1    = 1 hour
1.5  = 1 hour 30 minutes
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

produces:

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

Each generated message is submitted to Telegram as an individual server-side scheduled message.

### Schedule preview and confirmation

Before messages are submitted, Shuttle Scheduler displays the destination, message contents, generated schedule, and total number of messages.

The user must explicitly confirm the operation before anything is scheduled.

### Server-side scheduling

Shuttle Scheduler does **not** stay running until each message needs to be sent.

The workflow is:

```text
Configure schedule
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

There is no need for a continuously running Python process, cron job, cloud server, or background scheduler for messages that have already been submitted successfully to Telegram.

## Current limitations

The current version supports **one destination per scheduling operation**.

For example, you can select one private chat or one Telegram group and schedule multiple messages for that destination.

Selecting multiple groups or chats in a single scheduling operation is not yet supported.

## Requirements

* Python 3
* Telegram account
* Telegram API ID and API Hash
* Telethon
* python-dotenv

The project uses a Python virtual environment (`venv`) for dependency isolation.

## Installation

Clone the repository and enter the project directory:

```bash
git clone <YOUR-REPOSITORY-URL>
cd shuttle-scheduler
```

Create a virtual environment:

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

Install the required packages:

```bash
pip install -r requirements.txt
```

## Telegram API credentials

Shuttle Scheduler requires Telegram API credentials for your own Telegram account.

Create an application through:

https://my.telegram.org/

Then create a local `.env` file in the project directory:

```text
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

**Never commit this file to Git.**

The repository's `.gitignore` should exclude `.env`.

## First authentication

The first time the application authenticates with Telegram, Telethon may request:

* Your Telegram phone number
* A Telegram login verification code
* Your Two-Step Verification password, if enabled

After successful authentication, Telethon creates a local session file.

For this project it is typically:

```text
shuttle_scheduler.session
```

This session allows subsequent runs to authenticate without requesting a new verification code each time.

## ⚠️ Security

The following files contain sensitive information and must never be committed, uploaded, or shared:

```text
.env
*.session
*.session-journal
```

The `.env` file contains Telegram API credentials.

The Telethon `.session` file represents an authenticated Telegram session and should be treated like a credential.

The virtual environment should also remain local:

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

Before pushing changes to a public or private repository, verify what Git is tracking:

```bash
git ls-files
```

Make sure `.env`, `.venv/`, and all `.session` files are absent.

## Usage

Activate the virtual environment.

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Start Shuttle Scheduler:

```bash
python scheduler.py
```

Follow the interactive prompts to:

1. Select a Telegram destination.
2. Enter the message.
3. Choose single or interval scheduling.
4. Configure the schedule.
5. Review the generated schedule.
6. Confirm submission.

After the scheduled messages have been submitted, the application disconnects from Telegram and displays:

```text
Session disconnected.
```

Telegram then handles delivery of the scheduled messages.

## Time zone

The current application uses:

```text
Asia/Singapore
```

for scheduling and schedule previews.

## Responsible use

Shuttle Scheduler operates through an authenticated Telegram **user account**, not a Telegram bot.

It should only be used in chats and groups where the account is normally permitted to post.

The application does not attempt to bypass Telegram permissions or group restrictions.

Automated or high-volume messaging may be subject to Telegram limits and policies. Use reasonable scheduling frequencies and comply with Telegram's Terms of Service and the rules of the groups in which you participate.

## Project status

Current working functionality:

* [x] Telegram user authentication
* [x] Persistent local Telethon session
* [x] Saved Messages support
* [x] Private chat discovery and selection
* [x] Telegram group discovery and selection
* [x] Multiline custom messages
* [x] Single scheduled messages
* [x] Interval scheduling
* [x] Configurable daily scheduling window
* [x] Decimal-hour intervals
* [x] Multiple consecutive scheduling days
* [x] Schedule preview
* [x] Explicit confirmation
* [x] Telegram server-side scheduling
* [x] Submission result reporting
* [x] Explicit session disconnection
* [ ] Multiple destinations in one scheduling operation

## Planned next step

The next major feature is **multi-destination scheduling**.

The goal is to allow multiple Telegram groups or chats to be selected and apply one message and scheduling configuration across those destinations while retaining a complete preview and explicit confirmation before submission.

Example:

```text
Select groups:

[1] Saturday Badminton
[2] SG Badminton Kakis
[3] Tampines Badminton
[4] Bedok Games

Select one or more:
> 1,2,4
```

The application will then calculate and display the total number of Telegram messages that will be scheduled across all selected destinations before anything is submitted.

## License

No license has been specified yet.
