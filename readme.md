# Website Uptime Monitor

A lightweight Python3 service that checks a website's availability at fixed intervals, logs latency, writes a minimal HTML status page, and emails an alert when the site is unreachable. It installs itself as a `systemd` unit so it restarts automatically after crashes or reboots.

---

## Files

    monitor.py                  main script
    config.json                 runtime configuration (user-supplied)
    website_monitor.log         rolling log (created at runtime)
    /var/www/html/index.html    live status page (created at runtime)
    website_monitor.lock        PID lock file (created at runtime)
    /etc/systemd/system/
     |-monitor_website.service  unit file (created at runtime)

---

## Requirements

-   Python 3.8 or newer
-   Linux with `systemd`
-   Gmail account with an **App Password**
-   Python packages: `requests`, `psutil`

Install the Python packages:

    pip install requests psutil

---

## Configuration

Create `config.json` in the same directory as `monitor.py`:

    {
      "website": "https://example.com",
      "alert": "receiver@example.com",
      "poll-interval": 10,
      "timeout": 3,
      "from_email": "sender@gmail.com",
      "key": "gmail-app-password (not gmail login passwrod)"
    }

-   `website` - URL to monitor
-   `alert` - address that receives alert emails
-   `poll-interval` - seconds between checks
-   `timeout` - seconds to wait before treating the request as failed
-   `from_email` - Gmail address that sends alerts
-   `key` - App Password for `from_email`

---

## Running

### Start (root required)

    sudo python3 monitor.py

This:

1. Writes `monitor_website.service` to `/etc/systemd/system/`
2. Enables and starts the service
3. Begins polling the configured `website`

### Stop

    sudo python3 monitor.py stop

Stops and disables the service and removes the lock file.

---

## Logs and Status

-   **Program log** `website_monitor.log`
-   **Status page** `/var/www/html/index.html`
-   **Lock file** `website_monitor.lock`
