from modeltranslation.translator import translator, TranslationOptions
from services.models import Category, Product


class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class ProductTranslationOptions(TranslationOptions):
    fields = ("name", "description")


translator.register(Category, CategoryTranslationOptions)
translator.register(Product, ProductTranslationOptions)
