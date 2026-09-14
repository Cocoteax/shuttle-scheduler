import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import sys
from typing import Any
import zoneinfo
from dotenv import load_dotenv
from telethon import TelegramClient, errors, functions, types

SESSION_NAME = "shuttle_scheduler"
SINGAPORE_TZ = zoneinfo.ZoneInfo("Asia/Singapore")
MAX_DAYS_LIMIT = 14


@dataclass
class Destination:
    """Resolved Telegram scheduling destination."""

    name: str  # Display name
    type: str  # "Saved Messages", "Private chat", "Group", or "Forum topic"
    entity: Any  # Telethon InputPeer or 'me'
    raw_entity: Any = None  # Telethon User, Chat, or Channel
    group_name: str | None = None
    topic_name: str | None = None
    topic_id: int | None = None


def format_telegram_error(exc: Exception) -> str:
    """Format Telegram RPC errors into user-friendly messages without exposing credentials."""
    if isinstance(exc, errors.ChatWriteForbiddenError):
        return "Insufficient posting permissions: You are not permitted to post in this chat/group."
    elif isinstance(exc, errors.UserBannedInChannelError):
        return "Posting restricted: You are restricted or banned from sending messages in this group."
    elif isinstance(exc, errors.ChatAdminRequiredError):
        return "Admin privileges required: Only group administrators may post or schedule messages here."
    elif isinstance(exc, errors.TopicDeletedError):
        return "Topic not found: The selected forum topic has been deleted."
    elif isinstance(exc, errors.ChannelForumMissingError):
        return "Forum missing: This supergroup does not have forum topics enabled."
    elif isinstance(exc, errors.ScheduleTooMuchError):
        return "Schedule limit reached: Telegram limit for scheduled messages in this chat has been exceeded."
    elif isinstance(exc, errors.ScheduleDateInvalidError):
        return "Invalid schedule date: Telegram rejected the scheduled delivery timestamp."
    elif isinstance(exc, errors.FloodWaitError):
        secs = getattr(exc, "seconds", None)
        wait_text = f"of {secs} seconds" if secs else "period"
        return f"Rate limited: Telegram requested a wait {wait_text} before sending more requests."
    elif isinstance(exc, errors.SlowModeWaitError):
        secs = getattr(exc, "seconds", None)
        wait_text = f"{secs} seconds" if secs else "required period"
        return f"Slow mode active: Please wait {wait_text} between messages in this chat."
    elif isinstance(exc, errors.RPCError):
        if getattr(exc, "message", None) == "TOPIC_CLOSED":
            return "Topic closed: This topic has been closed to new messages."
        elif getattr(exc, "message", None) == "TOPIC_DELETED":
            return "Topic deleted: The selected forum topic has been deleted."
        return f"Telegram RPC error: {exc.message}"
    else:
        return f"Error: {exc}"


def classify_dialog(dialog):
    """Classify a Telethon dialog into human-readable categories."""
    if dialog.is_user:
        if getattr(dialog.entity, "is_self", False):
            return "Saved Messages"
        elif getattr(dialog.entity, "bot", False):
            return "Bot"
        else:
            return "Private"
    elif dialog.is_group:
        return "Group"
    elif dialog.is_channel:
        return "Channel"
    else:
        return "Other"


async def check_can_send_to_entity(client, entity):
    """
    Check if the user has permission to send messages to the given entity (User, Chat, or Channel).
    Returns (can_send: bool, reason: str | None).
    """
    if getattr(entity, "deleted", False):
        return False, "This account has been deleted."
    if getattr(entity, "left", False):
        return False, "You have left or are not a member of this group."
    if getattr(entity, "deactivated", False):
        return False, "This group has been deactivated."

    # User's personal banned rights in this group/channel
    user_banned = getattr(entity, "banned_rights", None)
    if user_banned and getattr(user_banned, "send_messages", False):
        return False, "You are restricted from sending messages in this chat."

    # Default banned rights if user is not creator or admin
    is_creator = getattr(entity, "creator", False)
    admin_rights = getattr(entity, "admin_rights", None)
    if not is_creator and not admin_rights:
        default_banned = getattr(entity, "default_banned_rights", None)
        if default_banned and getattr(default_banned, "send_messages", False):
            return False, "This chat is read-only (messages restricted by group settings)."

    # Telethon participant permissions check
    try:
        perms = await client.get_permissions(entity)
        if perms:
            if perms.is_banned:
                p_banned = getattr(perms.participant, "banned_rights", None)
                if p_banned and getattr(p_banned, "send_messages", False):
                    return False, "You are restricted from sending messages in this chat."
                return False, "You are banned from this chat."
            if perms.has_left:
                return False, "You have left this chat."
    except Exception:
        # Fallback to server-side check on send
        pass

    return True, None


async def fetch_all_forum_topics(client, group_entity):
    """
    Retrieve all forum topics for a forum-enabled supergroup using Telethon's GetForumTopicsRequest.
    Handles pagination.
    Returns list of dicts: [{'id': int, 'title': str, 'closed': bool, 'hidden': bool}, ...]
    """
    topics = []
    seen_ids = set()
    offset_date = None
    offset_id = 0
    offset_topic = 0
    limit = 100

    while True:
        res = await client(
            functions.messages.GetForumTopicsRequest(
                peer=group_entity,
                offset_date=offset_date,
                offset_id=offset_id,
                offset_topic=offset_topic,
                limit=limit,
            )
        )

        if not res or not res.topics:
            break

        new_topics_found = 0
        last_topic = None

        for t in res.topics:
            last_topic = t
            if isinstance(t, types.ForumTopic):
                if t.id not in seen_ids:
                    seen_ids.add(t.id)
                    topics.append({
                        "id": t.id,
                        "title": t.title or ("General" if t.id == 1 else f"Topic {t.id}"),
                        "closed": bool(getattr(t, "closed", False)),
                        "hidden": bool(getattr(t, "hidden", False)),
                    })
                    new_topics_found += 1

        if len(res.topics) < limit or new_topics_found == 0 or last_topic is None:
            break

        offset_date = getattr(last_topic, "date", None)
        offset_id = getattr(last_topic, "top_message", getattr(last_topic, "id", 0))
        offset_topic = getattr(last_topic, "id", 0)

    return topics


async def select_topic_for_forum_group(
    client: TelegramClient,
    group_name: str,
    group_input_entity,
    group_raw_entity,
) -> Destination | None:
    """
    Display topic selection interface for a forum-enabled supergroup.
    Returns a resolved Destination object if a topic is selected, or None if user went back.
    """
    print(f"\nRetrieving topics for '{group_name}'...")
    try:
        topics = await fetch_all_forum_topics(client, group_input_entity)
    except Exception as exc:
        err_msg = format_telegram_error(exc)
        print(f"\nFailed to retrieve forum topics for '{group_name}': {err_msg}", file=sys.stderr)
        input("Press Enter to return...")
        return None

    if not topics:
        print(f"\nNo active forum topics found in '{group_name}'.")
        input("Press Enter to return...")
        return None

    while True:
        print("\n========================================")
        print("SELECT TOPIC")
        print("========================================")
        print(f"\nGroup:\n{group_name}\n")

        for idx, t in enumerate(topics, start=1):
            closed_label = " [Closed]" if t["closed"] else ""
            print(f"[{idx}] {t['title']}{closed_label}")

        print("\n[B] Back")
        print("[Q] Quit\n")

        sel = input("Select topic:\n> ").strip()

        if sel.lower() == "b":
            return None
        elif sel.lower() == "q":
            print("\nExiting Shuttle Scheduler.")
            sys.exit(0)

        if sel.isdigit():
            idx = int(sel)
            if 1 <= idx <= len(topics):
                chosen_topic = topics[idx - 1]
                if chosen_topic["closed"]:
                    is_admin = getattr(group_raw_entity, "creator", False) or getattr(
                        group_raw_entity, "admin_rights", None
                    )
                    if not is_admin:
                        print(
                            f"\nTopic '{chosen_topic['title']}' is closed. Only administrators can post here."
                        )
                        input("Press Enter to continue...")
                        continue

                return Destination(
                    name=f"{group_name} — {chosen_topic['title']}",
                    type="Forum topic",
                    entity=group_input_entity,
                    raw_entity=group_raw_entity,
                    group_name=group_name,
                    topic_name=chosen_topic["title"],
                    topic_id=chosen_topic["id"],
                )
            else:
                print(
                    f"Invalid selection. Please enter a number between 1 and {len(topics)}."
                )
        else:
            print("Invalid option. Please try again.")


def parse_interval_to_timedelta(interval_hours: float) -> timedelta:
    """Convert decimal hours interval into timedelta, avoiding floating-point drift."""
    if interval_hours <= 0:
        raise ValueError("Interval must be a positive number greater than 0.")
    total_seconds = int(round(interval_hours * 3600))
    if total_seconds < 60:
        raise ValueError("Interval must be at least 1 minute (0.0167 hours).")
    return timedelta(seconds=total_seconds)


def generate_interval_schedule(
    start_date,
    start_time,
    end_time,
    interval_hours: float,
    num_days: int,
    tz=SINGAPORE_TZ,
    current_time=None,
):
    """
    Generate an interval schedule grouped by calendar date.

    Each day runs independently starting at start_time and stepping by interval_hours
    as long as time <= end_time. Does not continue overnight.

    Returns:
        schedule_by_date: dict mapping datetime.date -> list of timezone-aware datetimes
        total_generated: int total count of future scheduled timestamps
        past_excluded: int count of timestamps excluded because they are in the past
    """
    if num_days < 1:
        raise ValueError("Number of days must be at least 1.")
    if num_days > MAX_DAYS_LIMIT:
        raise ValueError(
            f"Number of days cannot exceed {MAX_DAYS_LIMIT} for prototype safety."
        )
    if end_time < start_time:
        raise ValueError(
            "Daily end time must be at or after daily start time. Overnight intervals are not supported."
        )

    interval_td = parse_interval_to_timedelta(interval_hours)

    if current_time is None:
        current_time = datetime.now(tz)

    schedule_by_date = {}
    total_generated = 0
    past_excluded = 0

    for day_idx in range(num_days):
        day_date = start_date + timedelta(days=day_idx)
        day_start_dt = datetime.combine(day_date, start_time, tzinfo=tz)
        day_end_dt = datetime.combine(day_date, end_time, tzinfo=tz)

        day_times = []
        curr_dt = day_start_dt
        while curr_dt <= day_end_dt:
            if curr_dt > current_time:
                day_times.append(curr_dt)
                total_generated += 1
            else:
                past_excluded += 1
            curr_dt += interval_td

        schedule_by_date[day_date] = day_times

    return schedule_by_date, total_generated, past_excluded


def prompt_message():
    """Prompt the user for a multiline message terminated with /done."""
    print("\nEnter your message below.")
    print("Type /done on its own line when finished.\n")

    lines = []
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        if line.strip() == "/done":
            break
        lines.append(line)

    message = "\n".join(lines).strip()
    if not message:
        print("Message cannot be empty. Please enter your message again.")
        return prompt_message()
    return message


def prompt_single_schedule_time():
    """Prompt the user for a single date and time in Asia/Singapore timezone."""
    now = datetime.now(SINGAPORE_TZ)

    while True:
        print(f"\nCurrent time (Asia/Singapore): {now.strftime('%d/%m/%Y %H:%M')}")
        try:
            date_str = input("Date (DD/MM/YYYY):\n> ").strip()
            if not date_str:
                print("Date cannot be empty.")
                continue

            time_str = input("Time (24-hour HH:MM):\n> ").strip()
            if not time_str:
                print("Time cannot be empty.")
                continue

            dt_naive = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
            scheduled_dt = dt_naive.replace(tzinfo=SINGAPORE_TZ)

            now = datetime.now(SINGAPORE_TZ)
            if scheduled_dt <= now:
                print(
                    f"\nError: Scheduled time must be in the future. Current time is {now.strftime('%d/%m/%Y %H:%M')} Asia/Singapore. Please try again."
                )
                continue

            return scheduled_dt

        except ValueError as err:
            print(f"\nInvalid date or time format: {err}")
            print("Please use DD/MM/YYYY (e.g. 15/09/2026) and HH:MM (e.g. 15:30).")


def prompt_interval_parameters():
    """Prompt the user for interval schedule parameters in Asia/Singapore timezone."""
    while True:
        now = datetime.now(SINGAPORE_TZ)
        print("\n----------------------------------------")
        print("INTERVAL SCHEDULE CONFIGURATION")
        print("----------------------------------------")
        print(f"Current time (Asia/Singapore): {now.strftime('%d/%m/%Y %H:%M')}\n")

        # 1. Start date
        try:
            start_date_str = input("Start date (DD/MM/YYYY):\n> ").strip()
            if not start_date_str:
                print("Start date cannot be empty.")
                continue
            start_date = datetime.strptime(start_date_str, "%d/%m/%Y").date()
        except ValueError:
            print("Invalid date format. Please use DD/MM/YYYY (e.g. 15/09/2026).")
            continue

        # 2. Daily start time
        try:
            start_time_str = input("Daily start time (24-hour HH:MM):\n> ").strip()
            if not start_time_str:
                print("Start time cannot be empty.")
                continue
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
        except ValueError:
            print("Invalid time format. Please use 24-hour HH:MM (e.g. 09:00).")
            continue

        # 3. Daily end time
        try:
            end_time_str = input("Daily end time (24-hour HH:MM):\n> ").strip()
            if not end_time_str:
                print("End time cannot be empty.")
                continue
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            print("Invalid time format. Please use 24-hour HH:MM (e.g. 22:00).")
            continue

        if end_time < start_time:
            print(
                f"\nError: Daily end time ({end_time_str}) cannot be earlier than daily start time ({start_time_str})."
            )
            print("Overnight intervals are not supported. Please try again.")
            continue

        # 4. Interval in hours
        try:
            interval_str = input("Interval between messages in hours:\n> ").strip()
            if not interval_str:
                print("Interval cannot be empty.")
                continue
            interval_hours = float(interval_str)
            if interval_hours <= 0:
                print("Interval must be a positive number greater than 0.")
                continue
        except ValueError:
            print(
                "Invalid interval. Please enter a valid positive number (e.g. 0.5, 1, 1.5, 2)."
            )
            continue

        # 5. Number of days
        try:
            days_str = input(
                f"Number of days (1 to {MAX_DAYS_LIMIT}):\n> "
            ).strip()
            if not days_str:
                print("Number of days cannot be empty.")
                continue
            num_days = int(days_str)
            if num_days < 1 or num_days > MAX_DAYS_LIMIT:
                print(
                    f"Number of days must be a whole number between 1 and {MAX_DAYS_LIMIT} for safety."
                )
                continue
        except ValueError:
            print(
                f"Invalid number of days. Please enter a whole number between 1 and {MAX_DAYS_LIMIT}."
            )
            continue

        # Generate and validate schedule
        try:
            now = datetime.now(SINGAPORE_TZ)
            schedule_by_date, total_count, past_excluded = generate_interval_schedule(
                start_date=start_date,
                start_time=start_time,
                end_time=end_time,
                interval_hours=interval_hours,
                num_days=num_days,
                tz=SINGAPORE_TZ,
                current_time=now,
            )
        except ValueError as err:
            print(f"\nSchedule error: {err}")
            continue

        if total_count == 0:
            if past_excluded > 0:
                print(
                    f"\nError: All {past_excluded} generated time slots have already passed relative to current time ({now.strftime('%d/%m/%Y %H:%M')})."
                )
                print("Please choose a future start date or later times.")
            else:
                print(
                    "\nError: No valid time slots were generated with the given window and interval. Please check your inputs."
                )
            continue

        if past_excluded > 0:
            print(
                f"\n[Notice] {past_excluded} time slot(s) on or before current time ({now.strftime('%d/%m/%Y %H:%M')}) have already passed and were excluded."
            )

        return {
            "schedule_by_date": schedule_by_date,
            "total_count": total_count,
            "past_excluded": past_excluded,
            "start_time_str": start_time.strftime("%H:%M"),
            "end_time_str": end_time.strftime("%H:%M"),
            "interval_hours": interval_hours,
            "num_days": num_days,
        }


async def run_scheduling_workflow(
    client: TelegramClient,
    destination: Destination,
) -> bool:
    """
    Unified scheduling workflow shared across Saved Messages, Private chats, Groups, and Forum Topics.
    Returns True if completed and should exit, or False if user went back.
    """
    # 1. Message Entry
    message_text = prompt_message()

    # 2. Scheduling Mode
    while True:
        print("\n========================================")
        print("SCHEDULING MODE")
        print("========================================")
        print("\n[1] Single scheduled message")
        print("[2] Repeating interval schedule")
        print("[B] Back")
        print("[Q] Quit\n")

        mode_choice = input("Select:\n> ").strip()

        if mode_choice == "1":
            # Single scheduled message mode
            scheduled_dt = prompt_single_schedule_time()

            print("\n========================================")
            print("SCHEDULE CONFIRMATION")
            print("========================================")
            if destination.type == "Forum topic":
                print("\nDestination type:\nForum topic\n")
                print(f"Group:\n{destination.group_name}\n")
                print(f"Topic:\n{destination.topic_name}\n")
            else:
                print(f"\nDestination:\n{destination.name}\n")
                print(f"Type:\n{destination.type}\n")

            print(
                f"Scheduled:\n{scheduled_dt.strftime('%d/%m/%Y %H:%M')} Asia/Singapore\n"
            )
            print("Message:")
            print("----------------------------------------")
            print(message_text)
            print("----------------------------------------\n")

            while True:
                confirm = input("Schedule this message? (y/n):\n> ").strip().lower()
                if confirm in ("y", "yes"):
                    print("\nSubmitting scheduled message to Telegram servers...")
                    try:
                        send_kwargs = {"schedule": scheduled_dt}
                        if destination.topic_id is not None:
                            send_kwargs["reply_to"] = destination.topic_id

                        await client.send_message(
                            destination.entity,
                            message_text,
                            **send_kwargs,
                        )
                        print("\n========================================")
                        print("SCHEDULING COMPLETE")
                        print("========================================")
                        if destination.type == "Forum topic":
                            print("\nDestination type:\nForum topic")
                            print(f"\nGroup:\n{destination.group_name}")
                            print(f"\nTopic:\n{destination.topic_name}")
                        else:
                            print(f"\nDestination:\n{destination.name}")

                        print("\nSuccessfully scheduled:\n1")
                        print("\nFailed:\n0")
                        print(
                            f"\nFirst scheduled message:\n{scheduled_dt.strftime('%d/%m/%Y %H:%M')}"
                        )
                        print(
                            f"\nLast scheduled message:\n{scheduled_dt.strftime('%d/%m/%Y %H:%M')}\n"
                        )
                        return True
                    except Exception as exc:
                        err_msg = format_telegram_error(exc)
                        print(f"\nScheduling failed: {err_msg}", file=sys.stderr)
                        input("\nPress Enter to return to the menu...")
                        return False

                elif confirm in ("n", "no"):
                    print("\nScheduling cancelled.")
                    input("Press Enter to return to the menu...")
                    return False
                else:
                    print("Invalid input. Please enter 'y' for yes or 'n' for no.")

        elif mode_choice == "2":
            # Repeating interval schedule mode
            interval_data = prompt_interval_parameters()
            schedule_by_date = interval_data["schedule_by_date"]
            total_count = interval_data["total_count"]
            start_time_str = interval_data["start_time_str"]
            end_time_str = interval_data["end_time_str"]
            interval_hours = interval_data["interval_hours"]
            num_days = interval_data["num_days"]

            # Display schedule preview
            print("\n========================================")
            print("SCHEDULE PREVIEW")
            print("========================================")
            if destination.type == "Forum topic":
                print("\nDestination type:\nForum topic\n")
                print(f"Group:\n{destination.group_name}\n")
                print(f"Topic:\n{destination.topic_name}\n")
            else:
                print(f"\nDestination:\n{destination.name}\n")
                print(f"Type:\n{destination.type}\n")

            print("Message:")
            print("----------------------------------------")
            print(message_text)
            print("----------------------------------------\n")
            print(f"Interval:\nEvery {interval_hours:g} hours\n")
            print(f"Daily window:\n{start_time_str} - {end_time_str}\n")
            print(f"Days:\n{num_days}\n")
            print("Generated schedule:\n")

            all_scheduled_dts = []
            for day_idx, (day_date, times) in enumerate(
                schedule_by_date.items(), start=1
            ):
                date_formatted = day_date.strftime("%d/%m/%Y")
                print(f"DAY {day_idx} — {date_formatted}")
                if not times:
                    print("  (All times on this day have already passed)")
                else:
                    for t_idx, dt in enumerate(times, start=1):
                        print(f"[{t_idx}] {dt.strftime('%H:%M')}")
                        all_scheduled_dts.append(dt)
                print()

            print(f"Total messages to schedule:\n{total_count}")
            print("========================================\n")

            print("WARNING:")
            if destination.type == "Forum topic":
                print(
                    f"You are about to schedule {total_count} messages to:\nGroup: {destination.group_name}\nTopic: {destination.topic_name}\n"
                )
            else:
                print(
                    f"You are about to schedule {total_count} messages to:\n{destination.name}\n"
                )

            while True:
                confirm = (
                    input(f"Schedule all {total_count} messages? (y/n):\n> ")
                    .strip()
                    .lower()
                )
                if confirm in ("y", "yes"):
                    print(
                        f"\nSubmitting {total_count} scheduled messages to Telegram servers..."
                    )
                    success_count = 0
                    failed_count = 0

                    for dt in all_scheduled_dts:
                        try:
                            send_kwargs = {"schedule": dt}
                            if destination.topic_id is not None:
                                send_kwargs["reply_to"] = destination.topic_id

                            await client.send_message(
                                destination.entity,
                                message_text,
                                **send_kwargs,
                            )
                            success_count += 1
                        except Exception as exc:
                            failed_count += 1
                            err_msg = format_telegram_error(exc)
                            print(
                                f"Failed to schedule for {dt.strftime('%d/%m/%Y %H:%M')}: {err_msg}",
                                file=sys.stderr,
                            )

                    print("\n========================================")
                    print("SCHEDULING COMPLETE")
                    print("========================================")
                    if destination.type == "Forum topic":
                        print("\nDestination type:\nForum topic")
                        print(f"\nGroup:\n{destination.group_name}")
                        print(f"\nTopic:\n{destination.topic_name}")
                    else:
                        print(f"\nDestination:\n{destination.name}")

                    print(f"\nSuccessfully scheduled:\n{success_count}")
                    print(f"\nFailed:\n{failed_count}")

                    if success_count > 0:
                        print(
                            f"\nFirst scheduled message:\n{all_scheduled_dts[0].strftime('%d/%m/%Y %H:%M')}"
                        )
                        print(
                            f"\nLast scheduled message:\n{all_scheduled_dts[-1].strftime('%d/%m/%Y %H:%M')}"
                        )
                    print()
                    return True

                elif confirm in ("n", "no"):
                    print("\nScheduling cancelled. 0 messages scheduled.")
                    input("Press Enter to return to the menu...")
                    return False
                else:
                    print("Invalid input. Please enter 'y' for yes or 'n' for no.")

        elif mode_choice.lower() == "b":
            return False

        elif mode_choice.lower() == "q":
            print("\nExiting Shuttle Scheduler.")
            sys.exit(0)

        else:
            print("Invalid option. Please choose 1, 2, B, or Q.")


async def main():
    # Load environment variables
    load_dotenv()

    api_id_raw = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id_raw or not api_id_raw.strip():
        print("Error: TELEGRAM_API_ID is missing or not set in .env", file=sys.stderr)
        sys.exit(1)

    if not api_hash or not api_hash.strip():
        print("Error: TELEGRAM_API_HASH is missing or not set in .env", file=sys.stderr)
        sys.exit(1)

    try:
        api_id = int(api_id_raw.strip())
    except ValueError:
        print(
            f"Error: TELEGRAM_API_ID must be an integer, got: {api_id_raw.strip()!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    api_hash = api_hash.strip()

    client = TelegramClient(SESSION_NAME, api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print(
                "Error: Session is not authorized. Please run test_connection.py first.",
                file=sys.stderr,
            )
            return

        # Retrieve dialogs
        print("Retrieving chats from Telegram...")
        dialogs = await client.get_dialogs()

        # Categorize dialogs
        private_chats = []
        groups = []
        channels = []
        all_chats = []

        # Ensure Saved Messages is accessible
        saved_messages_entry = {
            "name": "Saved Messages",
            "type": "Saved Messages",
            "entity": "me",
            "raw_entity": None,
            "schedulable": True,
        }

        for d in dialogs:
            category = classify_dialog(d)
            display_name = (
                d.name.strip() if d.name and d.name.strip() else f"Chat {d.id}"
            )

            if category == "Private":
                private_chats.append(d)
                all_chats.append({
                    "name": display_name,
                    "type": "Private chat",
                    "entity": d.input_entity,
                    "raw_entity": d.entity,
                    "schedulable": True,
                })
            elif category == "Group":
                groups.append(d)
                all_chats.append({
                    "name": display_name,
                    "type": "Group",
                    "entity": d.input_entity,
                    "raw_entity": d.entity,
                    "schedulable": True,
                })
            elif category == "Channel":
                channels.append(d)
                all_chats.append({
                    "name": display_name,
                    "type": "Channel",
                    "entity": d.input_entity,
                    "raw_entity": d.entity,
                    "schedulable": False,
                })
            elif category == "Bot":
                all_chats.append({
                    "name": display_name,
                    "type": "Bot",
                    "entity": d.input_entity,
                    "raw_entity": d.entity,
                    "schedulable": False,
                })
            elif category == "Saved Messages":
                pass

        # Main interactive loop
        while True:
            print("\n========================================")
            print("🏸 SHUTTLE SCHEDULER")
            print("========================================")
            print("\nWhat would you like to schedule to?\n")
            print("[1] Saved Messages")
            print("[2] Private chats")
            print("[3] Groups")
            print("[4] All available chats")
            print("[Q] Quit\n")

            choice = input("Select:\n> ").strip()

            destination: Destination | None = None

            if choice == "1":
                destination = Destination(
                    name="Saved Messages",
                    type="Saved Messages",
                    entity="me",
                )

            elif choice == "2":
                while True:
                    print("\nPRIVATE CHATS\n")
                    if not private_chats:
                        print("No private chats found.")
                        print("\n[B] Back\n[Q] Quit\n")
                    else:
                        for idx, pc in enumerate(private_chats, start=1):
                            name = (
                                pc.name.strip()
                                if pc.name and pc.name.strip()
                                else f"User {pc.id}"
                            )
                            print(f"[{idx}] {name}")
                        print("\n[B] Back")
                        print("[Q] Quit\n")

                    sel = input("Select a private chat:\n> ").strip()
                    if sel.lower() == "b":
                        break
                    elif sel.lower() == "q":
                        return

                    if private_chats and sel.isdigit():
                        idx = int(sel)
                        if 1 <= idx <= len(private_chats):
                            chosen = private_chats[idx - 1]
                            pc_name = (
                                chosen.name.strip()
                                if chosen.name and chosen.name.strip()
                                else f"User {chosen.id}"
                            )

                            # Validate recipient permissions
                            can_send, reason = await check_can_send_to_entity(
                                client, chosen.entity
                            )
                            if not can_send:
                                print(
                                    f"\nCannot schedule to '{pc_name}': {reason}"
                                )
                                input("Press Enter to continue...")
                                continue

                            destination = Destination(
                                name=pc_name,
                                type="Private chat",
                                entity=chosen.input_entity,
                                raw_entity=chosen.entity,
                            )
                            break
                        else:
                            print(
                                f"Invalid selection. Please enter a number between 1 and {len(private_chats)}."
                            )
                    else:
                        print("Invalid option. Please try again.")

                if not destination:
                    continue

            elif choice == "3":
                while True:
                    print("\nGROUPS\n")
                    if not groups:
                        print("No groups found.")
                        print("\n[B] Back\n[Q] Quit\n")
                    else:
                        for idx, grp in enumerate(groups, start=1):
                            name = (
                                grp.name.strip()
                                if grp.name and grp.name.strip()
                                else f"Group {grp.id}"
                            )
                            print(f"[{idx}] {name}")
                        print("\n[B] Back")
                        print("[Q] Quit\n")

                    sel = input("Select a group:\n> ").strip()
                    if sel.lower() == "b":
                        break
                    elif sel.lower() == "q":
                        return

                    if groups and sel.isdigit():
                        idx = int(sel)
                        if 1 <= idx <= len(groups):
                            chosen = groups[idx - 1]
                            grp_name = (
                                chosen.name.strip()
                                if chosen.name and chosen.name.strip()
                                else f"Group {chosen.id}"
                            )

                            # Validate group posting permissions
                            can_send, reason = await check_can_send_to_entity(
                                client, chosen.entity
                            )
                            if not can_send:
                                print(
                                    f"\nCannot schedule to '{grp_name}': {reason}"
                                )
                                input("Press Enter to continue...")
                                continue

                            # Detect whether it is a forum group
                            is_forum = getattr(chosen.entity, "forum", False)
                            if is_forum:
                                destination = await select_topic_for_forum_group(
                                    client=client,
                                    group_name=grp_name,
                                    group_input_entity=chosen.input_entity,
                                    group_raw_entity=chosen.entity,
                                )
                                if not destination:
                                    continue
                                break
                            else:
                                destination = Destination(
                                    name=grp_name,
                                    type="Group",
                                    entity=chosen.input_entity,
                                    raw_entity=chosen.entity,
                                    group_name=grp_name,
                                )
                                break
                        else:
                            print(
                                f"Invalid selection. Please enter a number between 1 and {len(groups)}."
                            )
                    else:
                        print("Invalid option. Please try again.")

                if not destination:
                    continue

            elif choice == "4":
                full_list = [saved_messages_entry] + all_chats
                while True:
                    print("\nALL AVAILABLE CHATS\n")
                    for idx, chat in enumerate(full_list, start=1):
                        print(f"[{idx}] {chat['name']} [{chat['type']}]")

                    print("\n[B] Back")
                    print("[Q] Quit\n")

                    sel = input("Select a chat:\n> ").strip()
                    if sel.lower() == "b":
                        break
                    elif sel.lower() == "q":
                        return

                    if sel.isdigit():
                        idx = int(sel)
                        if 1 <= idx <= len(full_list):
                            chosen = full_list[idx - 1]
                            if not chosen["schedulable"]:
                                print(
                                    f"\nScheduling to {chosen['type']} is not supported."
                                )
                                input("Press Enter to return to the menu...")
                                break
                            else:
                                if chosen.get("raw_entity"):
                                    can_send, reason = await check_can_send_to_entity(
                                        client, chosen["raw_entity"]
                                    )
                                    if not can_send:
                                        print(
                                            f"\nCannot schedule to '{chosen['name']}': {reason}"
                                        )
                                        input("Press Enter to continue...")
                                        continue

                                # Check if it is a forum group
                                if chosen["type"] == "Group":
                                    is_forum = getattr(
                                        chosen["raw_entity"], "forum", False
                                    )
                                    if is_forum:
                                        destination = await select_topic_for_forum_group(
                                            client=client,
                                            group_name=chosen["name"],
                                            group_input_entity=chosen["entity"],
                                            group_raw_entity=chosen["raw_entity"],
                                        )
                                        if not destination:
                                            continue
                                        break
                                    else:
                                        destination = Destination(
                                            name=chosen["name"],
                                            type="Group",
                                            entity=chosen["entity"],
                                            raw_entity=chosen["raw_entity"],
                                            group_name=chosen["name"],
                                        )
                                        break
                                else:
                                    destination = Destination(
                                        name=chosen["name"],
                                        type=chosen["type"],
                                        entity=chosen["entity"],
                                        raw_entity=chosen.get("raw_entity"),
                                    )
                                    break
                        else:
                            print(
                                f"Invalid selection. Please enter a number between 1 and {len(full_list)}."
                            )
                    else:
                        print("Invalid option. Please try again.")

                if not destination:
                    continue

            elif choice.lower() == "q":
                print("\nExiting Shuttle Scheduler.")
                return

            else:
                print("Invalid option. Please choose 1, 2, 3, 4, or Q.")
                continue

            # Run unified scheduling workflow
            completed = await run_scheduling_workflow(
                client=client,
                destination=destination,
            )
            if completed:
                return

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
    finally:
        try:
            if client.is_connected():
                await client.disconnect()
            if not client.is_connected():
                print("Session disconnected.")
            else:
                print("Disconnection error: client remains connected.", file=sys.stderr)
        except Exception as exc:
            print(f"Disconnection error: {exc}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
