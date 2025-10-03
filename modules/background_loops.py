from threading import Thread
from modules.reminider_watcher import check_reminders_loop
from modules.notification_watcher import watch_notifications_loop

def start_background_threads():
    reminder_thread = Thread(target=check_reminders_loop, daemon=True)
    notification_thread = Thread(target=watch_notifications_loop, daemon=True)

    reminder_thread.start()
    notification_thread.start()

    print("✅ Background threads started: Reminder & Notification Watchers.")
