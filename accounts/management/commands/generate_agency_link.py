from django.core.management.base import BaseCommand
from accounts.models import BotUser


class Command(BaseCommand):
    help = "Generate an agency invitation link for a specific agency user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--agency-id",
            type=int,
            help="Agency user ID to generate link for",
        )
        parser.add_argument(
            "--name",
            type=str,
            help="Name for the new agency profile to create",
        )
        parser.add_argument(
            "--phone",
            type=str,
            help="Phone number for the new agency profile",
        )
        parser.add_argument(
            "--language",
            type=str,
            default="uz",
            choices=["uz", "ru", "en"],
            help="Language preference for the agency (default: uz)",
        )

    def handle(self, *args, **options):
        agency_id = options.get("agency_id")
        name = options.get("name")
        phone = options.get("phone")
        language = options.get("language", "uz")

        # Create new agency or get existing one
        if name and phone:
            # Create new agency profile
            try:
                agency = BotUser.objects.create(
                    name=name,
                    phone=phone,
                    language=language,
                    is_agency=True,
                    is_active=True,  # Agency profiles are active by default
                    is_used=False,
                    step=5,  # Fully registered
                )
                self.stdout.write(
                    self.style.SUCCESS(f"\n✅ Successfully created agency profile:")
                )
                self.stdout.write(f"   ID: {agency.id}")
                self.stdout.write(f"   Name: {agency.name}")
                self.stdout.write(f"   Phone: {agency.phone}")
                self.stdout.write(f"   Language: {agency.language}")
                self.stdout.write(f"   Token: {agency.agency_token}")
                self.stdout.write(f"\n🔗 Invitation Link:")
                self.stdout.write(f"   {agency.agency_link}\n")
                self.stdout.write(
                    self.style.WARNING("⚠️  This link can only be used once!")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating agency profile: {str(e)}")
                )
                return

        elif agency_id:
            # Get existing agency
            try:
                agency = BotUser.objects.get(id=agency_id, is_agency=True)

                if agency.is_used:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\n⚠️  This agency invitation has already been used!"
                        )
                    )
                    if agency.agency_users.exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f"   Linked to user: {agency.agency_users.first().display_name}"
                            )
                        )
                    self.stdout.write(
                        self.style.WARNING(
                            "\nTo generate a new link, you need to create a new agency profile.\n"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"\n✅ Agency Profile Details:")
                    )
                    self.stdout.write(f"   ID: {agency.id}")
                    self.stdout.write(f"   Name: {agency.name}")
                    self.stdout.write(f"   Phone: {agency.phone}")
                    self.stdout.write(f"   Language: {agency.language}")
                    self.stdout.write(f"   Token: {agency.agency_token}")
                    self.stdout.write(
                        f'   Status: {"Used" if agency.is_used else "Available"}'
                    )
                    self.stdout.write(f"\n🔗 Invitation Link:")
                    self.stdout.write(f"   {agency.agency_link}\n")
                    self.stdout.write(
                        self.style.WARNING("⚠️  This link can only be used once!")
                    )

            except BotUser.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Agency with ID {agency_id} not found or is not an agency profile."
                    )
                )
                return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error retrieving agency: {str(e)}")
                )
                return
        else:
            self.stdout.write(
                self.style.ERROR(
                    "\n❌ Please provide either:\n"
                    "   1. --agency-id <id> to get an existing agency link, or\n"
                    "   2. --name <name> --phone <phone> to create a new agency profile\n"
                )
            )
            return
