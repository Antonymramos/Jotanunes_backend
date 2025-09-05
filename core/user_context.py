
import threading
_local = threading.local()

def set_user(user):  # chamado pelo middleware
    _local.user = user

def get_user():      # usado nos signals
    return getattr(_local, "user", None)
