# Reminder worker

Runs `community.usp_DeliverDueReminders` every 15 seconds using the backend image and SQL configuration.

```powershell
docker compose up -d worker
docker compose logs -f worker
```

The SQL transaction locks due rows, creates one inbox entry per permitted active recipient and marks the reminder sent. A unique `(ReminderId, UserId)` constraint prevents duplicate inbox entries. Failed transactions roll back and the next pass retries. Guest/inactive accounts and unrelated families receive nothing; personal reminders reach only their owner. Cancelling a pending reminder excludes it from later dispatch.

`EventReminders.Status=sent` means the SQL inbox has been processed. Android local alerts are scheduled by the Flutter app, not by this worker. They need notification permission and a prior sync. Remote FCM push is not configured. Existing inbox entries remain readable only while the account retains family access.

For a demo, create a future event, set a reminder two or three minutes ahead, enable Android notifications in the app and check the SQL inbox plus worker logs when due. See [the mobile guide](../mobile/README.md) and [delivery notes](../../docs/community-mobile.md).
