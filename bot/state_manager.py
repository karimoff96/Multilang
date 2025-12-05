"""
Bot State Manager - Handles persistent user state for multi-worker deployments.

This module provides a clean interface to store and retrieve user state data
using the BotUserState model instead of in-memory dictionaries.

Usage:
    from bot.state_manager import StateManager
    
    # Get state manager for a user
    state = StateManager.get(user_id, center_id)
    
    # Store/retrieve data
    state.set('order_id', 123)
    order_id = state.get('order_id')
    
    # Work with files
    state.add_file(file_id)
    files = state.get_files()
    
    # Clear on completion
    state.clear()
"""

import logging
from django.db import transaction
from django.core.cache import cache

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages bot user state with database persistence and optional Redis caching.
    
    This replaces the in-memory user_data and uploaded_files dictionaries
    to support multi-worker deployments where state must be shared.
    """
    
    # Cache timeout in seconds (5 minutes)
    CACHE_TIMEOUT = 300
    
    def __init__(self, bot_user):
        self.bot_user = bot_user
        self._state = None
        self._cache_key = f"bot_state:{bot_user.id}"
    
    @classmethod
    def get(cls, user_id, center_id=None):
        """
        Get StateManager for a user by telegram user_id.
        
        Args:
            user_id: Telegram user ID
            center_id: Optional center ID for multi-tenant lookup
            
        Returns:
            StateManager instance or None if user not found
        """
        from accounts.models import BotUser
        
        try:
            if center_id:
                bot_user = BotUser.objects.get(user_id=user_id, center_id=center_id)
            else:
                bot_user = BotUser.objects.filter(user_id=user_id).first()
            
            if bot_user:
                return cls(bot_user)
            return None
        except BotUser.DoesNotExist:
            return None
    
    @classmethod
    def get_for_bot_user(cls, bot_user):
        """Get StateManager for an existing BotUser instance"""
        return cls(bot_user)
    
    @property
    def state(self):
        """Lazy-load the state model with caching"""
        if self._state is None:
            # Try cache first
            cached = cache.get(self._cache_key)
            if cached:
                self._state = cached
            else:
                from accounts.models import BotUserState
                self._state, _ = BotUserState.objects.get_or_create(
                    bot_user=self.bot_user
                )
                cache.set(self._cache_key, self._state, self.CACHE_TIMEOUT)
        return self._state
    
    def _invalidate_cache(self):
        """Invalidate the cache after updates"""
        cache.delete(self._cache_key)
        self._state = None
    
    def refresh(self):
        """Force refresh state from database"""
        self._invalidate_cache()
        return self.state
    
    # ==========================================================================
    # Core getters/setters using extra_data JSON field
    # ==========================================================================
    
    def get(self, key, default=None):
        """Get a value from extra_data"""
        return self.state.extra_data.get(key, default)
    
    def set(self, key, value):
        """Set a value in extra_data"""
        self.state.extra_data[key] = value
        self.state.save(update_fields=['extra_data', 'updated_at'])
        self._invalidate_cache()
    
    def delete(self, key):
        """Delete a key from extra_data"""
        if key in self.state.extra_data:
            del self.state.extra_data[key]
            self.state.save(update_fields=['extra_data', 'updated_at'])
            self._invalidate_cache()
    
    # ==========================================================================
    # Order-related state
    # ==========================================================================
    
    @property
    def current_order(self):
        return self.state.current_order
    
    @current_order.setter
    def current_order(self, order):
        self.state.current_order = order
        self.state.save(update_fields=['current_order', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def category_id(self):
        return self.state.selected_category_id
    
    @category_id.setter
    def category_id(self, value):
        self.state.selected_category_id = value
        self.state.save(update_fields=['selected_category_id', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def product_id(self):
        return self.state.selected_product_id
    
    @product_id.setter
    def product_id(self, value):
        self.state.selected_product_id = value
        self.state.save(update_fields=['selected_product_id', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def language_id(self):
        return self.state.selected_language_id
    
    @language_id.setter
    def language_id(self, value):
        self.state.selected_language_id = value
        self.state.save(update_fields=['selected_language_id', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def copy_number(self):
        return self.state.copy_number
    
    @copy_number.setter
    def copy_number(self, value):
        self.state.copy_number = value or 0
        self.state.save(update_fields=['copy_number', 'updated_at'])
        self._invalidate_cache()
    
    # ==========================================================================
    # File upload tracking
    # ==========================================================================
    
    def get_files(self):
        """Get list of uploaded file IDs"""
        return self.state.uploaded_file_ids or []
    
    def add_file(self, file_id):
        """Add a file ID to the upload list"""
        if file_id:
            files = self.state.uploaded_file_ids or []
            if file_id not in files:
                self.state.uploaded_file_ids = files + [file_id]
                self.state.save(update_fields=['uploaded_file_ids', 'updated_at'])
                self._invalidate_cache()
    
    def clear_files(self):
        """Clear all uploaded files"""
        self.state.uploaded_file_ids = []
        self.state.save(update_fields=['uploaded_file_ids', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def total_pages(self):
        return self.state.total_pages
    
    @total_pages.setter
    def total_pages(self, value):
        self.state.total_pages = value or 0
        self.state.save(update_fields=['total_pages', 'updated_at'])
        self._invalidate_cache()
    
    # ==========================================================================
    # Message tracking for cleanup
    # ==========================================================================
    
    def get_message_ids(self):
        """Get list of message IDs for cleanup"""
        return self.state.message_ids or []
    
    def add_message_id(self, message_id):
        """Add a message ID for later cleanup"""
        if message_id:
            ids = self.state.message_ids or []
            if message_id not in ids:
                self.state.message_ids = ids + [message_id]
                self.state.save(update_fields=['message_ids', 'updated_at'])
                self._invalidate_cache()
    
    def clear_message_ids(self):
        """Clear message ID list after cleanup"""
        self.state.message_ids = []
        self.state.save(update_fields=['message_ids', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def totals_message_id(self):
        return self.state.totals_message_id
    
    @totals_message_id.setter
    def totals_message_id(self, value):
        self.state.totals_message_id = value
        self.state.save(update_fields=['totals_message_id', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def last_instruction_message_id(self):
        return self.state.last_instruction_message_id
    
    @last_instruction_message_id.setter
    def last_instruction_message_id(self, value):
        self.state.last_instruction_message_id = value
        self.state.save(update_fields=['last_instruction_message_id', 'updated_at'])
        self._invalidate_cache()
    
    # ==========================================================================
    # Payment tracking
    # ==========================================================================
    
    @property
    def pending_payment_order_id(self):
        return self.state.pending_payment_order_id
    
    @pending_payment_order_id.setter
    def pending_payment_order_id(self, value):
        self.state.pending_payment_order_id = value
        self.state.save(update_fields=['pending_payment_order_id', 'updated_at'])
        self._invalidate_cache()
    
    @property
    def pending_receipt_order_id(self):
        return self.state.pending_receipt_order_id
    
    @pending_receipt_order_id.setter
    def pending_receipt_order_id(self, value):
        self.state.pending_receipt_order_id = value
        self.state.save(update_fields=['pending_receipt_order_id', 'updated_at'])
        self._invalidate_cache()
    
    # ==========================================================================
    # Bulk operations
    # ==========================================================================
    
    def update(self, **kwargs):
        """Update multiple fields at once"""
        update_fields = ['updated_at']
        
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
                update_fields.append(key)
            else:
                # Store in extra_data
                self.state.extra_data[key] = value
                if 'extra_data' not in update_fields:
                    update_fields.append('extra_data')
        
        self.state.save(update_fields=update_fields)
        self._invalidate_cache()
    
    def clear(self):
        """Clear all order-related state"""
        self.state.clear_order_state()
        self._invalidate_cache()
    
    def to_dict(self):
        """Export state as dictionary (for debugging)"""
        return {
            'bot_user_id': self.bot_user.id,
            'current_order_id': self.state.current_order_id if self.state.current_order else None,
            'category_id': self.state.selected_category_id,
            'product_id': self.state.selected_product_id,
            'language_id': self.state.selected_language_id,
            'copy_number': self.state.copy_number,
            'uploaded_file_ids': self.state.uploaded_file_ids,
            'total_pages': self.state.total_pages,
            'message_ids': self.state.message_ids,
            'pending_payment_order_id': self.state.pending_payment_order_id,
            'pending_receipt_order_id': self.state.pending_receipt_order_id,
            'extra_data': self.state.extra_data,
        }


# =============================================================================
# Legacy compatibility layer
# =============================================================================
# These functions provide backward compatibility with the old user_data and 
# uploaded_files dictionaries. Use StateManager directly for new code.

def get_user_data(user_id, center_id=None):
    """Legacy: Get user_data dict-like interface"""
    state = StateManager.get(user_id, center_id)
    if state:
        return state.state.extra_data
    return {}


def set_user_data(user_id, key, value, center_id=None):
    """Legacy: Set a value in user_data"""
    state = StateManager.get(user_id, center_id)
    if state:
        state.set(key, value)


def get_uploaded_files(user_id, center_id=None):
    """Legacy: Get uploaded files dict"""
    state = StateManager.get(user_id, center_id)
    if state:
        return {
            'files': state.get_files(),
            'total_pages': state.total_pages,
            'totals_message_id': state.totals_message_id,
            'order_id': state.get('order_id'),
            'message_ids': state.get_message_ids(),
            'pending_payment_order_id': state.pending_payment_order_id,
        }
    return {}


def clear_user_state(user_id, center_id=None):
    """Legacy: Clear all user state"""
    state = StateManager.get(user_id, center_id)
    if state:
        state.clear()
