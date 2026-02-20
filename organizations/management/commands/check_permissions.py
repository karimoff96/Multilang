"""
Management command to diagnose and fix permission issues for users.

Usage:
    python manage.py check_permissions --username admin_user
    python manage.py check_permissions --all
    python manage.py check_permissions --fix --username admin_user
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from organizations.models import AdminUser, Role


class Command(BaseCommand):
    help = 'Check and diagnose permission issues for admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to check permissions for',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Check all non-superuser staff accounts',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix permission issues',
        )
        parser.add_argument(
            '--grant-staff-permissions',
            type=str,
            help='Grant staff management permissions to user (username)',
        )

    def handle(self, *args, **options):
        if options['grant_staff_permissions']:
            self.grant_staff_permissions(options['grant_staff_permissions'])
            return

        if options['username']:
            self.check_user(options['username'], options['fix'])
        elif options['all']:
            self.check_all_users(options['fix'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --username or --all')
            )

    def check_user(self, username, fix=False):
        """Check permissions for a specific user"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found')
            )
            return

        self.stdout.write(f'\n{self.style.SUCCESS("="*60)}')
        self.stdout.write(f'{self.style.SUCCESS(f"Checking user: {username}")}')
        self.stdout.write(f'{self.style.SUCCESS("="*60)}\n')

        # Check basic user properties
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Is superuser: {user.is_superuser}')
        self.stdout.write(f'Is staff: {user.is_staff}')
        self.stdout.write(f'Is active: {user.is_active}')

        # Check for AdminUser profile
        try:
            admin_profile = user.admin_profile
            self.stdout.write(f'\n{self.style.SUCCESS("✓ Has AdminUser profile")}')
            self.stdout.write(f'  Center: {admin_profile.center}')
            self.stdout.write(f'  Branch: {admin_profile.branch}')
            self.stdout.write(f'  Is active: {admin_profile.is_active}')

            # Check role
            if admin_profile.role:
                self.stdout.write(f'\n{self.style.SUCCESS("✓ Has role assigned")}')
                self.stdout.write(f'  Role: {admin_profile.role.display_name}')
                self.stdout.write(f'  Role active: {admin_profile.role.is_active}')

                # Check staff permissions
                staff_permissions = {
                    'can_view_staff': admin_profile.role.can_view_staff,
                    'can_create_staff': admin_profile.role.can_create_staff,
                    'can_edit_staff': admin_profile.role.can_edit_staff,
                    'can_delete_staff': admin_profile.role.can_delete_staff,
                    'can_manage_staff': admin_profile.role.can_manage_staff,
                }

                self.stdout.write(f'\n{self.style.WARNING("Staff Permissions:")}')
                has_any_staff_perm = False
                for perm, value in staff_permissions.items():
                    status = self.style.SUCCESS('✓') if value else self.style.ERROR('✗')
                    self.stdout.write(f'  {status} {perm}: {value}')
                    if value:
                        has_any_staff_perm = True

                # Check using has_permission method
                self.stdout.write(f'\n{self.style.WARNING("Permission Check Method Results:")}')
                for perm in ['can_view_staff', 'can_create_staff', 'can_manage_staff']:
                    result = admin_profile.has_permission(perm)
                    status = self.style.SUCCESS('✓') if result else self.style.ERROR('✗')
                    self.stdout.write(f'  {status} has_permission("{perm}"): {result}')

                if not has_any_staff_perm:
                    self.stdout.write(f'\n{self.style.ERROR("⚠ WARNING: User has no staff management permissions!")}')
                    if fix:
                        self.fix_user_permissions(user, admin_profile)
                else:
                    self.stdout.write(f'\n{self.style.SUCCESS("✓ User can manage staff")}')

            else:
                self.stdout.write(f'\n{self.style.ERROR("✗ No role assigned to AdminUser")}')
                if fix:
                    self.fix_missing_role(user, admin_profile)

        except AttributeError:
            self.stdout.write(f'\n{self.style.ERROR("✗ No AdminUser profile found")}')
            if fix:
                self.fix_missing_profile(user)

    def check_all_users(self, fix=False):
        """Check all non-superuser staff accounts"""
        users = User.objects.filter(is_staff=True, is_superuser=False)
        self.stdout.write(f'\nFound {users.count()} non-superuser staff accounts\n')

        for user in users:
            self.check_user(user.username, fix)
            self.stdout.write('\n')

    def fix_user_permissions(self, user, admin_profile):
        """Grant staff management permissions to user's role"""
        self.stdout.write(f'\n{self.style.WARNING("Attempting to fix permissions...")}')
        
        role = admin_profile.role
        role.can_view_staff = True
        role.can_create_staff = True
        role.can_edit_staff = True
        role.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Granted staff management permissions to role "{role.display_name}"'
            )
        )

    def fix_missing_role(self, user, admin_profile):
        """Assign a default role to admin profile"""
        self.stdout.write(f'\n{self.style.WARNING("Attempting to assign a role...")}')

        # Try to find a manager role
        try:
            role = Role.objects.filter(name='manager', is_active=True).first()
            if not role:
                # Try to find any active role that's not owner
                role = Role.objects.filter(is_active=True).exclude(name='owner').first()
            
            if role:
                admin_profile.role = role
                admin_profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Assigned role "{role.display_name}" to user')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ No suitable roles found. Create a role first.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error assigning role: {str(e)}')
            )

    def fix_missing_profile(self, user):
        """Create AdminUser profile for user"""
        self.stdout.write(f'\n{self.style.WARNING("Attempting to create AdminUser profile...")}')
        self.stdout.write(
            self.style.ERROR(
                'Cannot auto-create AdminUser profile without center/branch/role information.\n'
                'Please create the profile manually through the admin interface.'
            )
        )

    def grant_staff_permissions(self, username):
        """Grant staff management permissions to a specific user"""
        try:
            user = User.objects.get(username=username)
            admin_profile = user.admin_profile
            
            if not admin_profile.role:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" has no role assigned')
                )
                return

            role = admin_profile.role
            role.can_view_staff = True
            role.can_create_staff = True
            role.can_edit_staff = True
            role.can_manage_staff = True
            role.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Granted full staff management permissions to "{username}"'
                )
            )
            self.stdout.write(f'  Role: {role.display_name}')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found')
            )
        except AttributeError:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" has no AdminUser profile')
            )
