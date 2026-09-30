from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    from audit.services import log_action
    log_action(
        user=user,
        action='LOGIN',
        description=f'User {user.email} logged in',
        request=request
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        from audit.services import log_action
        log_action(
            user=user,
            action='LOGOUT',
            description=f'User {user.email} logged out',
            request=request
        )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    from audit.services import log_action
    log_action(
        user=None,
        action='LOGIN_FAILED',
        description=f'Failed login attempt for {credentials.get("username", "unknown")}',
        request=request
    )
