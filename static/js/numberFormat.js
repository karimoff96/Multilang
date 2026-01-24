/**
 * Number formatting utilities for WowDash
 * Provides consistent number formatting across the application
 */

const NumberFormat = {
    /**
     * Format number with thousand separators (spaces)
     * @param {number} value - The number to format
     * @returns {string} Formatted number (e.g., 1 000 000)
     */
    formatWithSeparators: function(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '0';
        }
        
        const num = typeof value === 'string' ? parseFloat(value) : value;
        
        // Check if it's an integer
        if (num === Math.floor(num)) {
            return Math.floor(num).toLocaleString('en-US').replace(/,/g, ' ');
        }
        
        // For decimals, format with 2 decimal places
        return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    },

    /**
     * Shorten number with K/M suffixes for lists and statistics
     * @param {number} value - The number to shorten
     * @returns {string} Shortened number (e.g., 1.2M, 5K)
     */
    shorten: function(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '0';
        }
        
        const num = typeof value === 'string' ? parseFloat(value) : value;
        const absNum = Math.abs(num);
        
        if (absNum >= 1000000) {
            const millions = num / 1000000;
            if (absNum >= 10000000) {
                return Math.round(millions) + 'M';
            }
            return (millions % 1 === 0) ? millions + 'M' : millions.toFixed(1) + 'M';
        } else if (absNum >= 1000) {
            const thousands = num / 1000;
            if (absNum >= 10000) {
                return Math.round(thousands) + 'K';
            }
            return (thousands % 1 === 0) ? thousands + 'K' : thousands.toFixed(1) + 'K';
        } else {
            return Math.round(num).toString();
        }
    },

    /**
     * Format currency with UZS suffix
     * @param {number} value - The amount
     * @param {boolean} short - Whether to use short format
     * @returns {string} Formatted currency
     */
    formatCurrency: function(value, short = false) {
        if (short) {
            return this.shorten(value) + ' UZS';
        }
        return this.formatWithSeparators(value) + ' UZS';
    },

    /**
     * Apply formatting to all elements with data-format attribute
     * data-format="full" - Full number with separators
     * data-format="short" - Shortened with K/M
     */
    applyFormatting: function() {
        // Format elements with data-format="full"
        document.querySelectorAll('[data-format="full"]').forEach(function(element) {
            const value = parseFloat(element.textContent.replace(/[^0-9.-]/g, ''));
            if (!isNaN(value)) {
                element.textContent = NumberFormat.formatWithSeparators(value);
            }
        });

        // Format elements with data-format="short"
        document.querySelectorAll('[data-format="short"]').forEach(function(element) {
            const value = parseFloat(element.textContent.replace(/[^0-9.-]/g, ''));
            if (!isNaN(value)) {
                element.textContent = NumberFormat.shorten(value);
            }
        });

        // Format elements with data-format="currency"
        document.querySelectorAll('[data-format="currency"]').forEach(function(element) {
            const value = parseFloat(element.textContent.replace(/[^0-9.-]/g, ''));
            const short = element.getAttribute('data-format-short') === 'true';
            if (!isNaN(value)) {
                element.textContent = NumberFormat.formatCurrency(value, short);
            }
        });
    }
};

// Auto-apply formatting on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        NumberFormat.applyFormatting();
    });
} else {
    NumberFormat.applyFormatting();
}

// Make it globally available
window.NumberFormat = NumberFormat;
