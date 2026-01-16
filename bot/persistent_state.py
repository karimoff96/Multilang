"""
Persistent State Dictionaries for Multi-Worker Bot Deployments.

This module provides drop-in replacements for the in-memory user_data and 
uploaded_files dictionaries. It uses Django's cache backend (Redis in production)
to share state across multiple Gunicorn workers.

Usage:
    # Instead of:
    # user_data = {}
    # uploaded_files = {}
    
    # Use:
    from bot.persistent_state import user_data, uploaded_files
    
    # Works exactly the same way:
    user_data[user_id] = {"key": "value"}
    value = user_data[user_id]["key"]
    
    if user_id in uploaded_files:
        files = uploaded_files[user_id]["files"]
"""

import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache key prefixes
USER_DATA_PREFIX = "bot_user_data:"
UPLOADED_FILES_PREFIX = "bot_uploaded_files:"

# Cache timeout: 24 hours (order flow should complete within this time)
CACHE_TIMEOUT = 86400


class AutoSaveDict(dict):
    """
    A dict subclass that automatically saves to cache when modified.
    """
    
    def __init__(self, cache_key, initial_data=None):
        self._cache_key = cache_key
        super().__init__(initial_data or {})
    
    def _save(self):
        """Save current state to cache"""
        cache.set(self._cache_key, dict(self), CACHE_TIMEOUT)
        logger.debug(f"Saved to cache: {self._cache_key} = {dict(self)}")
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._save()
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self._save()
    
    def pop(self, key, *args):
        result = super().pop(key, *args)
        self._save()
        return result
    
    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]
    
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._save()
    
    def clear(self):
        super().clear()
        self._save()


class PersistentUserDict:
    """
    A dictionary-like object that stores user data in Django's cache backend.
    
    This allows state to be shared across multiple Gunicorn workers when
    using Redis as the cache backend.
    
    Usage:
        user_data[user_id]["key"] = "value"  # Auto-saves
        user_data[user_id] = {"key": "value"}  # Also auto-saves
        
        if user_id in user_data:
            data = user_data[user_id]
    """
    
    def __init__(self, prefix):
        self.prefix = prefix
        self._local_cache = {}  # Keep references to AutoSaveDict instances
    
    def _get_key(self, user_id):
        return f"{self.prefix}{user_id}"
    
    def _get_or_create(self, user_id):
        """Get existing AutoSaveDict or create new one from cache"""
        cache_key = self._get_key(user_id)
        
        # Check if we already have a reference
        if user_id in self._local_cache:
            return self._local_cache[user_id]
        
        # Load from cache or create new
        cached_data = cache.get(cache_key)
        auto_save_dict = AutoSaveDict(cache_key, cached_data)
        self._local_cache[user_id] = auto_save_dict
        return auto_save_dict
    
    def __contains__(self, user_id):
        """Check if user_id has data: `if user_id in dict`"""
        cached = cache.get(self._get_key(user_id))
        return cached is not None and len(cached) > 0
    
    def __getitem__(self, user_id):
        """Get user data dict: `data = dict[user_id]`"""
        return self._get_or_create(user_id)
    
    def __setitem__(self, user_id, value):
        """Set user data: `dict[user_id] = {...}`"""
        cache_key = self._get_key(user_id)
        auto_save_dict = AutoSaveDict(cache_key, value)
        self._local_cache[user_id] = auto_save_dict
        auto_save_dict._save()
    
    def __delitem__(self, user_id):
        """Delete user data: `del dict[user_id]`"""
        cache.delete(self._get_key(user_id))
        self._local_cache.pop(user_id, None)
    
    def get(self, user_id, default=None):
        """Get with default: `dict.get(user_id, {})`"""
        cached = cache.get(self._get_key(user_id))
        if cached is not None:
            return self._get_or_create(user_id)
        return default
    
    def pop(self, user_id, default=None):
        """Pop user data: `dict.pop(user_id, None)`"""
        cache_key = self._get_key(user_id)
        data = cache.get(cache_key)
        if data is not None:
            cache.delete(cache_key)
            self._local_cache.pop(user_id, None)
            return data
        return default
    
    def setdefault(self, user_id, default=None):
        """Set default if not exists"""
        if user_id not in self:
            self[user_id] = default if default is not None else {}
        return self[user_id]
    
    def clear_local_cache(self):
        """Clear local references (useful for long-running processes)"""
        self._local_cache.clear()


# =============================================================================
# Global instances - drop-in replacements for the original dicts
# =============================================================================

user_data = PersistentUserDict(USER_DATA_PREFIX)
uploaded_files = PersistentUserDict(UPLOADED_FILES_PREFIX)


# =============================================================================
# Utility functions
# =============================================================================

def clear_user_state(user_id):
    """Clear all state for a user"""
    cache.delete(f"{USER_DATA_PREFIX}{user_id}")
    cache.delete(f"{UPLOADED_FILES_PREFIX}{user_id}")
    user_data.clear_local_cache()
    uploaded_files.clear_local_cache()


def get_all_user_state(user_id):
    """Get all state for debugging"""
    return {
        'user_data': cache.get(f"{USER_DATA_PREFIX}{user_id}", {}),
        'uploaded_files': cache.get(f"{UPLOADED_FILES_PREFIX}{user_id}", {}),
    }


def debug_state(user_id):
    """Debug helper to print current state"""
    state = get_all_user_state(user_id)
    logger.info(f"User {user_id} state: {state}")
    return state
