from modeltranslation.translator import translator, TranslationOptions
from .models import Region, District


class RegionTranslationOptions(TranslationOptions):
    fields = ('name',)


class DistrictTranslationOptions(TranslationOptions):
    fields = ('name',)


translator.register(Region, RegionTranslationOptions)
translator.register(District, DistrictTranslationOptions)
