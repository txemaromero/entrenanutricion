"""gunicorn settings, read from the working directory (backend/ on Render, /app in the image).

The access log keeps what operations need (method, path, status, size and time) and leaves out
what can be personal or secret: the query string (searches by name, the address asked to
/auth/email-exists), the referrer (the reset and confirmation pages carry their token in the URL)
and the user agent.
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(B)s %(M)sms'
