from modeltranslation.translator import translator, TranslationOptions
from .models import AdditionalInfo


class AdditionalInfoTranslationOptions(TranslationOptions):
    fields = ("help_text", "about_us")


translator.register(AdditionalInfo, AdditionalInfoTranslationOptions)
