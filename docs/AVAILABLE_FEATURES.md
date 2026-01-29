# Available Features for Tariff Plans

## Overview

This document provides a comprehensive catalog of **37 verified, working features** that can be assigned to tariff plans. All features listed have been validated against the codebase or are marked as available upon special request.

**Total Features:** 37 features across 10 categories

---

## 📊 1. Order Management Features (5)
**Dashboard Section:** Orders

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_orders_basic` | Basic Order Management | Create, view, and track customer orders | ✅ Implemented | All plans |
| `feature_orders_advanced` | Advanced Order Management | Bulk operations, advanced filters, export | ✅ Implemented | Pro, Enterprise |
| `feature_order_assignment` | Order Assignment | Assign orders to specific staff members | ✅ Implemented | Starter, Pro, Enterprise |
| `feature_bulk_payments` | Bulk Payment Processing | Process payments across multiple orders | ✅ Implemented | Pro, Enterprise |
| `feature_order_templates` | Order Templates | Save and reuse order configurations | ✅ Implemented | Enterprise |

---

## 📈 2. Analytics & Reports Features (6)
**Dashboard Section:** Reports

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_analytics_basic` | Basic Analytics | View order counts and basic statistics | ✅ Implemented | All plans |
| `feature_analytics_advanced` | Advanced Analytics | Detailed reports, financial analytics, trends | ✅ Implemented | Pro, Enterprise |
| `feature_financial_reports` | Financial Reports | Revenue, profit, expense analysis | ✅ Implemented | Pro, Enterprise |
| `feature_staff_performance` | Staff Performance Reports | Track individual staff productivity | ✅ Implemented | Pro, Enterprise |
| `feature_custom_reports` | Custom Report Builder | Create custom reports with filters | ✅ Implemented | Enterprise |
| `feature_export_reports` | Export Reports | Export to Excel, PDF, CSV formats | ✅ Implemented | Pro, Enterprise |

---

## 🔗 3. Integration Features (4)
**Dashboard Section:** Settings / Integrations

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_api_access` | REST API Access | REST API for custom integrations and automation | 🔧 On Request | Enterprise |
| `feature_webhooks` | Telegram Webhook Management | Configure and manage Telegram bot webhooks | ✅ Implemented | All plans |
| `feature_integrations` | Third-Party Integrations | Custom integrations with external services | 🔧 On Request | Enterprise |
| `feature_telegram_bot` | Telegram Bot Integration | Customer-facing bot for order placement | ✅ Implemented | All plans |

---

## 📢 4. Marketing & Communications Features (2)
**Dashboard Section:** Marketing

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_marketing_basic` | Marketing Campaign Tools | Create and manage marketing posts | ✅ Implemented | Pro, Enterprise |
| `feature_broadcast_messages` | Mass Broadcast Messaging | Send targeted broadcasts to customers | ✅ Implemented | Pro, Enterprise |

---

## 🏢 5. Organization & Staff Features (4)
**Dashboard Section:** Organizations

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_multi_branch` | Multiple Branches | Manage multiple branch locations | ✅ Implemented | Starter, Pro, Enterprise |
| `feature_custom_roles` | Custom Roles & Permissions | Create custom staff roles with RBAC | ✅ Implemented | Pro, Enterprise |
| `feature_staff_scheduling` | Staff Scheduling | Schedule and manage staff shifts | ✅ Implemented | Enterprise |
| `feature_branch_settings` | Branch Settings | Customize settings per branch | ✅ Implemented | Pro, Enterprise |

---

## 📦 6. Storage & Archive Features (3)
**Dashboard Section:** Core (Archive)

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_archive_access` | Historical File Archives | Access compressed archives of completed orders | ✅ Implemented | Pro, Enterprise |
| `feature_cloud_backup` | Automated Cloud Backups | Database and file backups to cloud storage | ✅ Implemented | Enterprise |
| `feature_extended_storage` | Extended Storage Capacity | Additional storage for documents and media | ✅ Implemented | Pro, Enterprise |

---

## 💰 7. Financial Management Features (4)
**Dashboard Section:** Finance

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_multi_currency` | Multi-Currency Pricing | Support for multiple currencies (UZS, USD, RUB) | ✅ Implemented | Pro, Enterprise |
| `feature_payment_management` | Payment Tracking & Recording | Manual payment recording and receipt verification | ✅ Implemented | All plans |
| `feature_invoicing` | Automated Invoicing | Generate invoices for orders | ✅ Implemented | Pro, Enterprise |
| `feature_expense_tracking` | Expense Tracking | Track business expenses by branch | ✅ Implemented | Pro, Enterprise |

---

## 🎯 8. Support & Services Features (2)
**Dashboard Section:** Services / Support

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_support_tickets` | Support Ticketing System | Internal ticketing for issue tracking | ✅ Implemented | Enterprise |
| `feature_knowledge_base` | Knowledge Base Access | Access to documentation and user guides | ✅ Implemented | All plans |

---

## ⚡ 9. Advanced Features (3)
**Dashboard Section:** Multiple sections

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_advanced_security` | Advanced Security Features | Enhanced security (audit logs, RBAC) | ✅ Implemented | Pro, Enterprise |
| `feature_audit_logs` | Comprehensive Audit Logs | Track all system actions and changes | ✅ Implemented | Pro, Enterprise |
| `feature_data_retention` | Data Retention Control | Configure data retention policies | ✅ Implemented | Enterprise |

---

## 🛠️ 10. Services Management Features (4)
**Dashboard Section:** Services

| Feature Code | Display Name | Description | Status | Typical Plans |
|-------------|--------------|-------------|--------|---------------|
| `feature_products_basic` | Basic Product Management | Manage services and basic pricing | ✅ Implemented | All plans |
| `feature_products_advanced` | Advanced Product Management | Complex pricing, categories, customization | ✅ Implemented | Pro, Enterprise |
| `feature_language_pricing` | Language-Specific Pricing | Different pricing per language combination | ✅ Implemented | Starter, Pro, Enterprise |
| `feature_dynamic_pricing` | Dynamic Pricing | Per-page pricing calculations | ✅ Implemented | All plans |

---

## Summary

- **Total Features:** 33
- **Fully Implemented:** 29 features (88%)
- **On Request:** 2 features (6%) - API Access, Third-Party Integrations
- **Documentation:** 2 features (6%) - Support Tickets, Knowledge Base

**Removed from Original 42:**
- Customer Segmentation (basic filtering only)
- Marketing Analytics (delivery stats only)
- Document Templates (not implemented)
- Priority Support (no priority system)
- Dedicated Account Manager (service offering)
- Training & Onboarding (no interactive system)
- Custom Development (service offering)
- White Label Branding (not implemented)
- Custom Domain (subdomain only)

---

## Feature Comparison Table

| Feature | Free Trial | Starter | Pro | Enterprise |
|---------|:----------:|:-------:|:---:|:----------:|
| **Orders (5)** | | | | |
| Basic Order Management | ✅ | ✅ | ✅ | ✅ |
| Advanced Order Management | ❌ | ❌ | ✅ | ✅ |
| Order Assignment | ❌ | ✅ | ✅ | ✅ |
| Bulk Payments | ❌ | ❌ | ✅ | ✅ |
| Order Templates | ❌ | ❌ | ❌ | ✅ |
| **Analytics (6)** | | | | |
| Basic Analytics | ✅ | ✅ | ✅ | ✅ |
| Advanced Analytics | ❌ | ❌ | ✅ | ✅ |
| Financial Reports | ❌ | ❌ | ✅ | ✅ |
| Staff Performance | ❌ | ❌ | ✅ | ✅ |
| Custom Reports | ❌ | ❌ | ❌ | ✅ |
| Export Reports | ❌ | ❌ | ✅ | ✅ |
| **Integration (4)** | | | | |
| Telegram Bot | ✅ | ✅ | ✅ | ✅ |
| Webhooks | ✅ | ✅ | ✅ | ✅ |
| REST API Access | ❌ | ❌ | ❌ | 🔧 |
| Third-Party Integrations | ❌ | ❌ | ❌ | 🔧 |
| **Marketing (2)** | | | | |
| Marketing Tools | ❌ | ❌ | ✅ | ✅ |
| Broadcast Messaging | ❌ | ❌ | ✅ | ✅ |
| **Organization (4)** | | | | |
| Multiple Branches | 1 | 3 | 10 | ∞ |
| Custom Roles | ❌ | ❌ | ✅ | ✅ |
| Staff Scheduling | ❌ | ❌ | ❌ | ✅ |
| Branch Settings | ❌ | ❌ | ✅ | ✅ |
| **Storage (3)** | | | | |
| Archive Access | ❌ | ✅ | ✅ | ✅ |
| Cloud Backup | ❌ | ❌ | ❌ | ✅ |
| Extended Storage | ❌ | ❌ | ✅ | ✅ |
| **Financial (4)** | | | | |
| Payment Management | ✅ | ✅ | ✅ | ✅ |
| Multi-Currency | ❌ | ❌ | ✅ | ✅ |
| Invoicing | ❌ | ❌ | ✅ | ✅ |
| Expense Tracking | ❌ | ❌ | ✅ | ✅ |
| **Support (2)** | | | | |
| Knowledge Base | ✅ | ✅ | ✅ | ✅ |
| Support Tickets | ❌ | ❌ | ❌ | ✅ |
| **Advanced (3)** | | | | |
| Advanced Security | ❌ | ❌ | ✅ | ✅ |
| Audit Logs | ❌ | ❌ | ✅ | ✅ |
| Data Retention | ❌ | ❌ | ❌ | ✅ |
| **Services (4)** | | | | |
| Basic Products | ✅ | ✅ | ✅ | ✅ |
| Advanced Products | ❌ | ❌ | ✅ | ✅ |
| Language Pricing | ❌ | ✅ | ✅ | ✅ |
| Dynamic Pricing | ✅ | ✅ | ✅ | ✅ |

**Legend:**
- ✅ = Included
- ❌ = Not included
- 🔧 = Available on special request
- ∞ = Unlimited

---

**Date:** January 29, 2026  
**Status:** ✅ Ready for implementation  
**Total Features:** 33 verified features
