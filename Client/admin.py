from django.contrib import admin
from django.forms import Select
from .models import BillingInfo,ClientInfo,RealTimeBill,Billing,MeterLog,Pricing,Notifications
from django_admin_inline_paginator.admin import TabularInlinePaginated
import datetime

#admin.site.register(BillingInfo)
#admin.site.register(RealTimeBill)

admin.site.register(Billing)

class tabularRealtime(TabularInlinePaginated):
    model = RealTimeBill
    fields = ('timestamp', 'totalconsumption', 'currentread') 
    per_page = 10
    
class Billings(TabularInlinePaginated):
    model = Billing
    fields = ('billingmonth', 'billingyear', 'totalconsumed') 
    per_page = 10 
    
class MeterlogDetail(TabularInlinePaginated):
    model = MeterLog
    fields = ('timestamp', 'meterid','currentread', 'totalconsumption')
    per_page = 10
    
@admin.register(ClientInfo)  
class CLientInforAdminWithPage(admin.ModelAdmin):
    list_display = ('meterid','fullname','switch','meterserial')
    inlines = (Billings,tabularRealtime,MeterlogDetail)
    model = ClientInfo
    
    @admin.display(description='Name')
    def fullname(self,obj):
        return ("%s %s" % (obj.firstname, obj.lastname)).upper()
    
    def save_model(self, request, obj, form, change):
        #obj.some_field = some_value # Update some_field with the desired value
        super().save_model(request, obj, form, change) # Call the superclass method to save the model
        notif = Notifications()
        if obj.isactive == False:
            notif.message = 'The admin has made your account inactive. Please check with the admin the status of your acount.'
        else:
            notif.message = 'The admin has activated your account.'

        notif.meterid_id = obj.id
        notif.timestamp = datetime.datetime.now()
        notif.isseen = False
        notif.save()
# Register your models here..re

@admin.register(RealTimeBill)
class RealTimeBillAdmin(admin.ModelAdmin):
    model = RealTimeBill
    list_display = ('timestamp', 'totalconsumption', 'currentread') 
    list_filter = ['meterid']
    
@admin.register(Pricing)  
class PricingAdmin(admin.ModelAdmin):
    model = Pricing
    list_display = ('rangefrom','rangeto','isflatrate','residentialrate','commercialrate1','commercialrate2','commercialrate3','commercialrate4','commercialrate5')

    
    
@admin.register(MeterLog)  
class MeterlogAdmin(admin.ModelAdmin):
    model = MeterLog
    list_display = ('timestamp', 'meterid','currentread', 'totalconsumption')

    
@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    model = Notifications
    verbose_name_plural = "Notification" 
    list_display = ('id', 'message', 'isseen') 
    
    
#class RealTimeBill(admin.TabularInline):
#    model = RealTimeBill
#    max_num = 10
#    min_num = 10
#    can_delete = False  
#    extra = 0
#    date_hierarchy = ('timestamp') 
#
#
#    def formfield_for_foreignkey(self, db_field, request, **kwargs):
#       if db_field.name == "timestamp":
#           kwargs["queryset"] =RealTimeBill.objects.all()
#           kwargs["widget"] = Select(attrs={"style": "width:400px"},)
#       return super().formfield_for_foreignkey(db_field, request, **kwargs)
# 
# 
#@admin.register(ClientInfo)  
#class CLientInforAdmin(admin.ModelAdmin):
#    list_display = ('meterid','fullname','switch','meterserial')
#    search_fields = ['lastname','meterid']
#    inlines = [
#        RealTimeBill
#    ]
#    @admin.display(description='Name')
#    def fullname(self,obj):
#        return ("%s %s" % (obj.firstname, obj.lastname)).upper()
    

