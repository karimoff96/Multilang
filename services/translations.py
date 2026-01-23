from modeltranslation.translator import translator, TranslationOptions
from services.models import Category, Product, Language


class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class LanguageTranslationOptions(TranslationOptions):
    fields = ('name',)


translator.register(Category, CategoryTranslationOptions)
translator.register(Product, ProductTranslationOptions)
translator.register(Language, LanguageTranslationOptions)
