from django.contrib import admin
from account.models import Accounts

# Register your models here.
@admin.register(Accounts)
class AccountsAdmin(admin.ModelAdmin):
    # Dynamically get all non-many-to-many field names
    list_display = [field.name for field in Accounts._meta.fields if field.name != "id"] 
    # The "id" field can be excluded if it's an AutoField
    

        
