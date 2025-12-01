"""
Reports & Analytics Views
Financial/order reports per branch/center with date filtering
"""

from django.shortcuts import render
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
import json

from orders.models import Order
from accounts.models import BotUser
from services.models import Product
from organizations.models import Branch, TranslationCenter, AdminUser
from organizations.rbac import get_user_orders, get_user_customers, get_user_branches


def financial_reports(request):
    """Financial reports view with revenue analytics"""
    # Date filters
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    branch_id = request.GET.get("branch")
    center_id = request.GET.get("center")

    today = timezone.now()
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    # Get orders based on user role
    all_orders = get_user_orders(request.user)

    # Apply date filters
    orders = all_orders.filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    )

    # Get available branches for filter
    branches = get_user_branches(request.user)

    # Center filter for superuser
    centers = None
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_id:
            orders = orders.filter(branch__center_id=center_id)
            branches = branches.filter(center_id=center_id)

    if branch_id:
        orders = orders.filter(branch_id=branch_id)

    # Calculate financial metrics
    total_revenue = float(orders.aggregate(total=Sum("total_price"))["total"] or 0)
    total_orders = orders.count()
    avg_order_value = float(orders.aggregate(avg=Avg("total_price"))["avg"] or 0)

    # Completed orders revenue
    completed_orders = orders.filter(status="completed")
    completed_revenue = float(
        completed_orders.aggregate(total=Sum("total_price"))["total"] or 0
    )

    # Daily revenue breakdown
    daily_revenue = (
        orders.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(revenue=Sum("total_price"), count=Count("id"))
        .order_by("date")
    )

    daily_labels = []
    daily_values = []
    daily_counts = []
    for item in daily_revenue:
        daily_labels.append(item["date"].strftime("%b %d"))
        daily_values.append(float(item["revenue"] or 0))
        daily_counts.append(item["count"])

    # Revenue by status
    status_breakdown = (
        orders.values("status")
        .annotate(revenue=Sum("total_price"), count=Count("id"))
        .order_by("-revenue")
    )

    status_data = []
    for item in status_breakdown:
        status_data.append(
            {
                "status": item["status"],
                "status_display": dict(Order.STATUS_CHOICES).get(
                    item["status"], item["status"]
                ),
                "revenue": float(item["revenue"] or 0),
                "count": item["count"],
            }
        )

    # Revenue by branch (if owner/superuser)
    branch_revenue = []
    if hasattr(request, "admin_profile") and request.admin_profile:
        if request.admin_profile.is_owner or request.user.is_superuser:
            branch_data = (
                orders.values("branch__name")
                .annotate(revenue=Sum("total_price"), count=Count("id"))
                .order_by("-revenue")[:10]
            )

            for item in branch_data:
                branch_revenue.append(
                    {
                        "branch": item["branch__name"] or "Unassigned",
                        "revenue": float(item["revenue"] or 0),
                        "count": item["count"],
                    }
                )

    # Top products by revenue
    top_products = (
        orders.values("product__name")
        .annotate(revenue=Sum("total_price"), count=Count("id"))
        .order_by("-revenue")[:5]
    )

    product_data = []
    for item in top_products:
        product_data.append(
            {
                "product": item["product__name"] or "Unknown",
                "revenue": float(item["revenue"] or 0),
                "count": item["count"],
            }
        )

    context = {
        "title": "Financial Reports",
        "subTitle": "Reports / Financial",
        # Filters
        "date_from": date_from,
        "date_to": date_to,
        "branches": branches,
        "selected_branch": branch_id,
        "centers": centers,
        "selected_center": center_id,
        # Metrics
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": avg_order_value,
        "completed_revenue": completed_revenue,
        # Chart data
        "daily_labels": json.dumps(daily_labels),
        "daily_values": json.dumps(daily_values),
        "daily_counts": json.dumps(daily_counts),
        # Breakdowns
        "status_data": status_data,
        "branch_revenue": branch_revenue,
        "product_data": product_data,
    }
    return render(request, "reports/financial.html", context)


def order_reports(request):
    """Order analytics and reports"""
    # Date filters
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    branch_id = request.GET.get("branch")
    status_filter = request.GET.get("status")
    center_id = request.GET.get("center")

    today = timezone.now()
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    # Get orders based on user role
    all_orders = get_user_orders(request.user)

    # Apply filters
    orders = all_orders.filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    )

    branches = get_user_branches(request.user)

    # Center filter for superuser
    centers = None
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_id:
            orders = orders.filter(branch__center_id=center_id)
            branches = branches.filter(center_id=center_id)

    if branch_id:
        orders = orders.filter(branch_id=branch_id)
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Order metrics
    total_orders = orders.count()
    completed = orders.filter(status="completed").count()
    cancelled = orders.filter(status="cancelled").count()
    in_progress = orders.filter(status="in_progress").count()
    pending = orders.filter(status__in=["pending", "ready"]).count()

    completion_rate = round(
        (completed / total_orders * 100) if total_orders > 0 else 0, 1
    )
    cancellation_rate = round(
        (cancelled / total_orders * 100) if total_orders > 0 else 0, 1
    )

    # Daily order counts
    daily_orders = (
        orders.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    daily_labels = [item["date"].strftime("%b %d") for item in daily_orders]
    daily_values = [item["count"] for item in daily_orders]

    # Orders by status breakdown for pie chart
    status_breakdown = (
        orders.values("status").annotate(count=Count("id")).order_by("-count")
    )

    status_labels = []
    status_values = []
    for item in status_breakdown:
        status_labels.append(
            dict(Order.STATUS_CHOICES).get(item["status"], item["status"])
        )
        status_values.append(item["count"])

    # Orders by language pair
    language_breakdown = (
        orders.values("language__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    language_data = []
    for item in language_breakdown:
        language_data.append(
            {"pair": item["language__name"] or "N/A", "count": item["count"]}
        )

    # Recent orders list
    recent_orders = orders.select_related(
        "bot_user", "product", "assigned_to__user"
    ).order_by("-created_at")[:20]

    context = {
        "title": "Order Reports",
        "subTitle": "Reports / Orders",
        # Filters
        "date_from": date_from,
        "date_to": date_to,
        "branches": branches,
        "selected_branch": branch_id,
        "selected_status": status_filter,
        "status_choices": Order.STATUS_CHOICES,
        "centers": centers,
        "selected_center": center_id,
        # Metrics
        "total_orders": total_orders,
        "completed": completed,
        "cancelled": cancelled,
        "in_progress": in_progress,
        "pending": pending,
        "completion_rate": completion_rate,
        "cancellation_rate": cancellation_rate,
        # Chart data
        "daily_labels": json.dumps(daily_labels),
        "daily_values": json.dumps(daily_values),
        "status_labels": json.dumps(status_labels),
        "status_values": json.dumps(status_values),
        # Breakdowns
        "language_data": language_data,
        "recent_orders": recent_orders,
    }
    return render(request, "reports/orders.html", context)


def staff_performance(request):
    """Staff performance reports - for managers and owners"""
    # Date filters
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    branch_id = request.GET.get("branch")
    center_id = request.GET.get("center")

    today = timezone.now()
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    # Get orders and branches based on user role
    all_orders = get_user_orders(request.user)
    branches = get_user_branches(request.user)

    # Center filter for superuser
    centers = None
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_id:
            all_orders = all_orders.filter(branch__center_id=center_id)
            branches = branches.filter(center_id=center_id)

    # Filter orders by date and branch
    orders = all_orders.filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    )

    if branch_id:
        orders = orders.filter(branch_id=branch_id)
        selected_branch = branches.filter(id=branch_id).first()
    else:
        selected_branch = None

    # Get staff members based on permissions
    if request.user.is_superuser:
        staff_members = AdminUser.objects.filter(is_active=True)
        if center_id:
            staff_members = staff_members.filter(branch__center_id=center_id)
    elif hasattr(request, "admin_profile") and request.admin_profile:
        if request.admin_profile.is_owner:
            staff_members = AdminUser.objects.filter(
                branch__center__owner=request.user, is_active=True
            )
        elif request.admin_profile.is_manager:
            staff_members = AdminUser.objects.filter(
                branch=request.admin_profile.branch, is_active=True
            )
        else:
            staff_members = AdminUser.objects.filter(pk=request.admin_profile.pk)
    else:
        staff_members = AdminUser.objects.none()

    if branch_id:
        staff_members = staff_members.filter(branch_id=branch_id)

    # Calculate performance for each staff member
    staff_data = []
    for staff in staff_members:
        staff_orders = orders.filter(assigned_to=staff)
        total_assigned = staff_orders.count()
        completed_orders = staff_orders.filter(status="completed").count()
        revenue = float(
            staff_orders.filter(status="completed").aggregate(total=Sum("total_price"))[
                "total"
            ]
            or 0
        )

        # Calculate average completion time (simplified - based on updated_at - created_at)
        completion_rate = round(
            (completed_orders / total_assigned * 100) if total_assigned > 0 else 0, 1
        )

        staff_data.append(
            {
                "id": staff.id,
                "name": staff.user.get_full_name() or staff.user.username,
                "center": (
                    staff.branch.center.name
                    if staff.branch and staff.branch.center
                    else "N/A"
                ),
                "branch": staff.branch.name if staff.branch else "N/A",
                "role": staff.role.name if staff.role else "Staff",
                "total_assigned": total_assigned,
                "completed": completed_orders,
                "revenue": revenue,
                "completion_rate": completion_rate,
            }
        )

    # Sort by completed orders
    staff_data.sort(key=lambda x: x["completed"], reverse=True)

    # Top performers
    top_performers = staff_data[:5] if staff_data else []

    # Staff performance chart data
    staff_labels = [s["name"] for s in top_performers]
    staff_completed = [s["completed"] for s in top_performers]
    staff_revenue = [s["revenue"] for s in top_performers]

    context = {
        "title": "Staff Performance",
        "subTitle": "Reports / Staff Performance",
        # Filters
        "date_from": date_from,
        "date_to": date_to,
        "branches": branches,
        "selected_branch": branch_id,
        "centers": centers,
        "selected_center": center_id,
        # Staff data
        "staff_data": staff_data,
        "top_performers": top_performers,
        # Chart data
        "staff_labels": json.dumps(staff_labels),
        "staff_completed": json.dumps(staff_completed),
        "staff_revenue": json.dumps(staff_revenue),
    }
    return render(request, "reports/staff_performance.html", context)


def branch_comparison(request):
    """Compare branch performance - for owners and superusers"""
    # Date filters
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    center_id = request.GET.get("center")

    today = timezone.now()
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    # Get branches based on user role
    branches = get_user_branches(request.user)
    all_orders = get_user_orders(request.user)

    # Center filter for superuser
    centers = None
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_id:
            branches = branches.filter(center_id=center_id)
            all_orders = all_orders.filter(branch__center_id=center_id)

    orders = all_orders.filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    )

    # Calculate metrics for each branch
    branch_data = []
    for branch in branches:
        branch_orders = orders.filter(branch=branch)
        total_orders = branch_orders.count()
        completed = branch_orders.filter(status="completed").count()
        revenue = float(branch_orders.aggregate(total=Sum("total_price"))["total"] or 0)
        avg_value = float(branch_orders.aggregate(avg=Avg("total_price"))["avg"] or 0)

        # Staff count
        staff_count = AdminUser.objects.filter(branch=branch, is_active=True).count()

        # Customer count
        customer_count = BotUser.objects.filter(branch=branch, is_active=True).count()

        branch_data.append(
            {
                "id": branch.id,
                "name": branch.name,
                "center": branch.center.name if branch.center else "N/A",
                "total_orders": total_orders,
                "completed": completed,
                "revenue": revenue,
                "avg_value": avg_value,
                "staff_count": staff_count,
                "customer_count": customer_count,
                "completion_rate": round(
                    (completed / total_orders * 100) if total_orders > 0 else 0, 1
                ),
            }
        )

    # Sort by revenue
    branch_data.sort(key=lambda x: x["revenue"], reverse=True)

    # Chart data
    branch_labels = [b["name"] for b in branch_data[:10]]
    branch_revenue = [b["revenue"] for b in branch_data[:10]]
    branch_orders_count = [b["total_orders"] for b in branch_data[:10]]

    # Summary
    total_revenue = sum(b["revenue"] for b in branch_data)
    total_orders_count = sum(b["total_orders"] for b in branch_data)
    total_staff = sum(b["staff_count"] for b in branch_data)
    total_customers = sum(b["customer_count"] for b in branch_data)

    context = {
        "title": "Branch Comparison",
        "subTitle": "Reports / Branch Comparison",
        # Filters
        "date_from": date_from,
        "date_to": date_to,
        "centers": centers,
        "selected_center": center_id,
        # Data
        "branch_data": branch_data,
        # Chart data
        "branch_labels": json.dumps(branch_labels),
        "branch_revenue": json.dumps(branch_revenue),
        "branch_orders_count": json.dumps(branch_orders_count),
        # Summary
        "total_revenue": total_revenue,
        "total_orders_count": total_orders_count,
        "total_staff": total_staff,
        "total_customers": total_customers,
    }
    return render(request, "reports/branch_comparison.html", context)


def customer_analytics(request):
    """Customer analytics - acquisition, retention, etc."""
    # Date filters
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    branch_id = request.GET.get("branch")
    center_id = request.GET.get("center")

    today = timezone.now()
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    # Get customers and orders based on user role
    customers = get_user_customers(request.user)
    orders = get_user_orders(request.user)
    branches = get_user_branches(request.user)

    # Center filter for superuser
    centers = None
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_id:
            # Filter customers who have orders in branches of this center
            customer_ids = (
                orders.filter(branch__center_id=center_id)
                .values_list("customer_id", flat=True)
                .distinct()
            )
            customers = customers.filter(id__in=customer_ids)
            orders = orders.filter(branch__center_id=center_id)
            branches = branches.filter(center_id=center_id)

    if branch_id:
        customers = customers.filter(branch_id=branch_id)
        orders = orders.filter(branch_id=branch_id)

    # Date range filter
    orders = orders.filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    )

    # Customer metrics
    total_customers = customers.count()
    active_customers = customers.filter(is_active=True).count()
    new_customers = customers.filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    ).count()

    agencies = customers.filter(is_agency=True).count()

    # Customer acquisition trend
    acquisition_data = (
        customers.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    acquisition_labels = [item["date"].strftime("%b %d") for item in acquisition_data]
    acquisition_values = [item["count"] for item in acquisition_data]

    # Top customers by orders
    top_customers = (
        orders.values("bot_user__id", "bot_user__name", "bot_user__is_agency")
        .annotate(order_count=Count("id"), total_spent=Sum("total_price"))
        .order_by("-total_spent")[:10]
    )

    top_customer_data = []
    for item in top_customers:
        top_customer_data.append(
            {
                "name": item["bot_user__name"] or "Unknown",
                "is_agency": item["bot_user__is_agency"],
                "order_count": item["order_count"],
                "total_spent": float(item["total_spent"] or 0),
            }
        )

    # Customer type breakdown
    type_breakdown = [
        {"type": "Agencies", "count": agencies},
        {"type": "Regular Customers", "count": total_customers - agencies},
    ]

    context = {
        "title": "Customer Analytics",
        "subTitle": "Reports / Customers",
        # Filters
        "date_from": date_from,
        "date_to": date_to,
        "branches": branches,
        "selected_branch": branch_id,
        "centers": centers,
        "selected_center": center_id,
        # Metrics
        "total_customers": total_customers,
        "active_customers": active_customers,
        "new_customers": new_customers,
        "agencies": agencies,
        # Chart data
        "acquisition_labels": json.dumps(acquisition_labels),
        "acquisition_values": json.dumps(acquisition_values),
        # Breakdowns
        "top_customers": top_customer_data,
        "type_breakdown": type_breakdown,
    }
    return render(request, "reports/customers.html", context)


def export_report(request, report_type):
    """Export report data as JSON (can be extended to CSV/Excel)"""
    import csv
    from django.http import HttpResponse

    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    today = timezone.now()
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    orders = get_user_orders(request.user).filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    )

    if report_type == "orders":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="orders_report_{date_from}_to_{date_to}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            ["Order ID", "Customer", "Product", "Status", "Total Price", "Created At"]
        )

        for order in orders.select_related("bot_user", "product"):
            writer.writerow(
                [
                    order.id,
                    order.bot_user.name if order.bot_user else "Unknown",
                    order.product.name if order.product else "Unknown",
                    order.get_status_display(),
                    order.total_price,
                    order.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        return response

    elif report_type == "financial":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="financial_report_{date_from}_to_{date_to}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(["Date", "Orders", "Revenue", "Avg Order Value"])

        daily_data = (
            orders.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                count=Count("id"), revenue=Sum("total_price"), avg=Avg("total_price")
            )
            .order_by("date")
        )

        for item in daily_data:
            writer.writerow(
                [
                    item["date"].strftime("%Y-%m-%d"),
                    item["count"],
                    float(item["revenue"] or 0),
                    float(item["avg"] or 0),
                ]
            )

        return response

    return JsonResponse({"error": "Invalid report type"}, status=400)


def my_statistics(request):
    """
    Personal statistics view for staff members.
    Shows only orders assigned to the current user.
    """
    from django.contrib.auth.decorators import login_required

    today = timezone.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    year_start = today_start.replace(month=1, day=1)

    # Get admin profile
    admin_profile = None
    if hasattr(request.user, "admin_profile"):
        admin_profile = request.user.admin_profile

    # Get only orders assigned to this user
    if admin_profile:
        my_orders = Order.objects.filter(assigned_to=admin_profile)
    else:
        my_orders = Order.objects.none()

    # Today's stats
    today_orders = my_orders.filter(created_at__gte=today_start)
    today_count = today_orders.count()
    today_completed = today_orders.filter(status="completed").count()
    today_pages = today_orders.aggregate(total=Sum("total_pages"))["total"] or 0

    # This week's stats
    week_orders = my_orders.filter(created_at__gte=week_start)
    week_count = week_orders.count()
    week_completed = week_orders.filter(status="completed").count()
    week_pages = week_orders.aggregate(total=Sum("total_pages"))["total"] or 0

    # This month's stats
    month_orders = my_orders.filter(created_at__gte=month_start)
    month_count = month_orders.count()
    month_completed = month_orders.filter(status="completed").count()
    month_pages = month_orders.aggregate(total=Sum("total_pages"))["total"] or 0

    # This year's stats
    year_orders = my_orders.filter(created_at__gte=year_start)
    year_count = year_orders.count()
    year_completed = year_orders.filter(status="completed").count()
    year_pages = year_orders.aggregate(total=Sum("total_pages"))["total"] or 0

    # All time stats
    total_count = my_orders.count()
    total_completed = my_orders.filter(status="completed").count()
    total_pages = my_orders.aggregate(total=Sum("total_pages"))["total"] or 0

    # Completion rate
    completion_rate = (
        round((total_completed / total_count * 100), 1) if total_count > 0 else 0
    )

    # Status breakdown for current month
    status_breakdown = (
        month_orders.values("status").annotate(count=Count("id")).order_by("-count")
    )

    STATUS_LABELS = {
        "pending": "Pending",
        "payment_pending": "Payment Pending",
        "payment_received": "Payment Received",
        "payment_confirmed": "Payment Confirmed",
        "in_progress": "In Progress",
        "ready": "Ready",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }

    STATUS_COLORS = {
        "pending": "#FF9F29",
        "payment_pending": "#6C757D",
        "payment_received": "#17A2B8",
        "payment_confirmed": "#28A745",
        "in_progress": "#487FFF",
        "ready": "#6F42C1",
        "completed": "#45B369",
        "cancelled": "#DC3545",
    }

    status_data = []
    for item in status_breakdown:
        status_data.append(
            {
                "status": item["status"],
                "label": STATUS_LABELS.get(item["status"], item["status"]),
                "count": item["count"],
                "color": STATUS_COLORS.get(item["status"], "#6C757D"),
            }
        )

    # Daily performance for the month (chart data)
    daily_performance = (
        month_orders.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"), pages=Sum("total_pages"))
        .order_by("date")
    )

    daily_labels = []
    daily_counts = []
    daily_pages = []
    for item in daily_performance:
        daily_labels.append(item["date"].strftime("%d"))
        daily_counts.append(item["count"])
        daily_pages.append(item["pages"] or 0)

    # Recent orders (last 10)
    recent_orders = my_orders.select_related("bot_user", "product").order_by(
        "-created_at"
    )[:10]

    context = {
        "title": "My Statistics",
        "subTitle": "Your Personal Performance",
        # Today
        "today_count": today_count,
        "today_completed": today_completed,
        "today_pages": today_pages,
        # Week
        "week_count": week_count,
        "week_completed": week_completed,
        "week_pages": week_pages,
        # Month
        "month_count": month_count,
        "month_completed": month_completed,
        "month_pages": month_pages,
        # Year
        "year_count": year_count,
        "year_completed": year_completed,
        "year_pages": year_pages,
        # All time
        "total_count": total_count,
        "total_completed": total_completed,
        "total_pages": total_pages,
        "completion_rate": completion_rate,
        # Chart data
        "status_data": json.dumps(status_data),
        "daily_labels": json.dumps(daily_labels),
        "daily_counts": json.dumps(daily_counts),
        "daily_pages": json.dumps(daily_pages),
        # Recent orders
        "recent_orders": recent_orders,
    }

    return render(request, "reports/my_statistics.html", context)
