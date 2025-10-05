from django.dispatch import Signal

# args: config, operation
pre_sync = Signal()
post_sync = Signal()
sync_failed = Signal()

__all__ = ["pre_sync", "post_sync", "sync_failed"]
