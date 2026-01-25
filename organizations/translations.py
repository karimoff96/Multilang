from modeltranslation.translator import translator, TranslationOptions
from organizations.models import TranslationCenter, Branch, Role


class TranslationCenterTranslationOptions(TranslationOptions):
    """Translation options for TranslationCenter model"""
    fields = ('name', 'address')


class BranchTranslationOptions(TranslationOptions):
    """Translation options for Branch model"""
    fields = ('name', 'address')


class RoleTranslationOptions(TranslationOptions):
    """Translation options for Role model"""
    fields = ('display_name', 'description')


translator.register(TranslationCenter, TranslationCenterTranslationOptions)
translator.register(Branch, BranchTranslationOptions)
translator.register(Role, RoleTranslationOptions)
