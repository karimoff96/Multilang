#!/usr/bin/env python
"""
Quick test script to verify agency invitation system
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WowDash.settings")
django.setup()

from accounts.models import BotUser


def main():
    print("\n" + "=" * 70)
    print("🔍 AGENCY INVITATION SYSTEM CHECK")
    print("=" * 70 + "\n")

    # Check environment variables
    bot_username = os.getenv("TELEGRAM_BOT_USERNAME")
    print(f"📋 Bot Username: {bot_username}")

    if not bot_username:
        print("❌ TELEGRAM_BOT_USERNAME not set in .env!")
        print("   Add: TELEGRAM_BOT_USERNAME=your_bot_username")
        return

    if bot_username.startswith("@"):
        print("⚠️  WARNING: Bot username starts with @")
        print("   Should be: developer_ro_bot")
        print("   Not: @developer_ro_bot")

    print()

    # List all agencies
    agencies = BotUser.objects.filter(is_agency=True)
    print(f"📊 Total Agency Profiles: {agencies.count()}\n")

    if not agencies.exists():
        print("❌ No agency profiles found!")
        print("\nCreate one with:")
        print("  python manage.py generate_agency_link \\")
        print('    --name "Test Agency" \\')
        print('    --phone "+998901234567" \\')
        print("    --language uz")
        return

    # Show each agency
    for i, agency in enumerate(agencies, 1):
        print(f"Agency #{i}")
        print("-" * 60)
        print(f"  ID: {agency.id}")
        print(f"  Name: {agency.name}")
        print(f"  Phone: {agency.phone}")
        print(f"  Language: {agency.language}")
        print(f"  Token: {agency.agency_token}")
        print(f"  Used: {'🔒 YES' if agency.is_used else '✅ NO (Available)'}")
        print(f"\n  📎 Invitation Link:")
        print(f"  {agency.agency_link}")

        # Show linked users
        linked_users = agency.agency_users.all()
        if linked_users.exists():
            print(f"\n  👥 Linked Users ({linked_users.count()}):")
            for user in linked_users:
                print(f"     - {user.name} (Telegram ID: {user.user_id})")
        else:
            print(f"\n  👥 Linked Users: None yet")

        # Show action
        if agency.is_used:
            print(f"\n  ⚠️  To reuse this link, reset it in admin:")
            print(f"     Admin → Users → Select agency → Reset invitation link")
        else:
            print(f"\n  ✅ This link is ready to use!")

        print()

    print("=" * 70)
    print("\n✅ Check complete!\n")

    # Summary
    unused_count = agencies.filter(is_used=False).count()
    used_count = agencies.filter(is_used=True).count()

    print("📈 Summary:")
    print(f"   Available invitations: {unused_count}")
    print(f"   Used invitations: {used_count}")
    print(f"   Total agencies: {agencies.count()}")

    # Show users linked to agencies
    agency_users = BotUser.objects.filter(agency__isnull=False)
    print(f"\n👥 Users linked to agencies: {agency_users.count()}")

    if agency_users.exists():
        print("\nAgency Users:")
        for user in agency_users:
            print(f"  - {user.name} → {user.agency.name if user.agency else 'None'}")

    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
