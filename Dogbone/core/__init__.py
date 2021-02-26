from core.tools import kick_my_other_sessions, kick_all_my_sessions
from django.contrib.auth.signals import user_logged_in, user_logged_out


user_logged_in.connect(kick_my_other_sessions)
user_logged_out.connect(kick_all_my_sessions)
