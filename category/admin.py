from django.contrib import admin
from . models import Category
# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('category_name',)}
    list_display_links=('category_name',)
    list_display=('category_name' ,'slug','description','cat_image')

    list_editable=('slug','description','cat_image')

admin.site.register(Category,CategoryAdmin)
