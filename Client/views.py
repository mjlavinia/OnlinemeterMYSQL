import calendar
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.template import loader
from django.urls import reverse
from .models import ClientInfo,RealTimeBill, BillingInfo, Billing,MeterLog,Notifications,Pricing
from django.views import generic
from .forms import NewUserForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
import datetime
from decimal import Decimal
import json
from .tool.functools import setLastMonth,setLastYear,setTimeNotifications
from django.core import serializers
from django.utils.timezone import localtime

@login_required(login_url='/accounts/login/')   
def index(request):
    context = None
    
    if request.user.is_authenticated and request.user.is_staff == False:
        template = loader.get_template('client/dashboard.html') 
        current_user = request.user 
        client = ClientInfo.objects.filter(user_id = current_user.id).first()
        if client != None:
            year = setLastYear(datetime.date.today().year, datetime.date.today().month)
            month = setLastMonth(datetime.date.today().month)
            billing = Billing.objects.filter(meterid_id = client.id, billingyear = year, billingmonth = month).first()
            if billing is None:
                billing = Billing.objects.filter(meterid_id = client.id, billingyear = year, billingmonth = month-1).first()
                   
            realtime = RealTimeBill.objects.filter(meterid_id = client.id, timestamp = datetime.date.today()).first()
            
        period =   calendar.month_name[billing.billingmonth] +' '+ str(client.billingday) + ',' + str(year) + " - " + calendar.month_name[billing.billingmonth +  1] +' '+  str(client.billingday) + ',' + str(year) 

        context = {
            'client' : client,  
            'billing': billing,
            'realtime': realtime,
            'user': current_user,
            'period':period,
            'readdate': calendar.month_name[billing.billingmonth] +' '+ str(client.billingday) + ',' + str(year),
            'prevtotal': billing.totalconsumed * Decimal(1.90)
        }
       
    else:
        if request.user.is_authenticated: 
            from django.contrib.auth import logout
            logout(request) 
        template = loader.get_template('registration/login.html')
    return HttpResponse(template.render(context,request)) 


def signup(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save( )
			login(request, user)
			messages.success(request, "Registration successful." )
			return redirect("main:homepage")
		messages.error(request, "errors")
	form = NewUserForm()
	return render (request=request, template_name="registration/signup.html", context={"register_form":form})


def dashboard(request):
    current_user = request
    template = loader.get_template('client/dashboard.html')
    client = ClientInfo.objects.filter(user_id = request.user.id).first()
    if client != None:
        billing = Billing.objects.filter(meterid_id = client.meterid).first()
   
    context = {
        'client' : client,  
        'billing': billing,
        'user': current_user
    }
    return HttpResponse(template.render(context, request))


def chart(request):
    current_user = request
    template = loader.get_template('client/chart.html')
    client = ClientInfo.objects.filter(user_id = request.user.id).first()
    start_date = datetime.datetime.now() - datetime.timedelta(30)
    if client != None:
        consumed_in_a_month = RealTimeBill.objects.filter(meterid_id =   client.id,timestamp__gte = start_date).all()
     
        cdata = serializers.serialize("json", list(consumed_in_a_month), fields = ("timestamp", "totalconsumption", "currentread"))

    context = {
        'client' : client,  
        'data': cdata   ,
        'user': current_user
    }  
    
    return HttpResponse(template.render(context, request))


def savemeter(request):
    try:
        id = request.GET.get('meterid')
        
        client = ClientInfo.objects.get(meterid = id)
        from django.utils import timezone
        now = timezone.now()
        
        
        if client:

            realtimeRecord = RealTimeBill.objects.filter(meterid_id = client.id, timestamp = datetime.date.today()).first()
            updateId = None
            msg = 'new record added'
            if realtimeRecord:
               updateId= realtimeRecord.id
               msg = 'update ID:' + str(updateId)
            
            total  = Decimal(request.GET.get('total'))
            current  = Decimal(request.GET.get('current'))
            newMeter = RealTimeBill(id = updateId ,meterid_id = client.id, totalconsumption = total, timestamp = datetime.date.today(), currentread = current)
            newMeter.switch = client.switch    
            addBillRecord(client.billingdate, newMeter)     
            
            if now.minute == 58:
                meterlog = MeterLog(meterid_id = client.id, totalconsumption = total, currentread = current)
                meterlog.timestamp = datetime.datetime.now()
                meterlog.save()  
                

        
        newMeter.save()
        return JsonResponse({'switch': str(client.switch), 'msg':msg})
    except Exception as e:
        return JsonResponse({'error': e.args})
    
def addBillRecord(billdate, realtime):
    if (billdate.day+ 1 == realtime.timestamp.day): 
        realtimeRecord = RealTimeBill.objects.filter(meterid_id = realtime.meterid_id, timestamp = realtime.timestamp- datetime.timedelta(days = 1)).first()
       
        year = setLastYear(realtime.timestamp.yearrealtime.timestamp.month)
        month = setLastYear(realtime.timestamp.month)
        listing = Billing.objects.filter(meterid_id = realtime.meterid_id, billingyear = year, billingmonth = month).first()
        
        if listing is None:           
            billinfo = Billing(meterid_id = realtime.meterid_id, totalconsumed = realtime.totalconsumption, billingyear = year, billingmonth = month)
            listing = billinfo
            
        listing.totalconsumed = realtimeRecord.totalconsumption    
        listing.save()
        
#@login_required(login_url='/accounts/login/')  


def settings(request,id):
    if request.user.is_authenticated:
        template = loader.get_template('client/updatesettings.html')
        client = ClientInfo.objects.filter(user_id = request.user.id).first()
        client.switchid = 1
        if client.switch:
                client.switchid = 2
                
        context = {'client' : client}
    
    else:
        template = loader.get_template('accounts/login.html')
    return HttpResponse(template.render(context,request))


@login_required(login_url='/accounts/login/')  


def notifications(request):
    if request.user.is_authenticated:
        param = request.GET.get('param')
        id = request.GET.get('id')
        clientid = param
        
        if id:
            notif = Notifications.objects.filter(id = id).order_by('-timestamp', 'isseen').all()
            savenotif = notif.first()
            savenotif.period = setTimeNotifications(savenotif.timestamp)
            clientid = savenotif.meterid_id
            savenotif.isseen = True
            savenotif.save()
            notif = [savenotif]
            
        else:
            notif = Notifications.objects.filter(meterid_id = param).order_by('-timestamp', 'isseen').all()[:10]
            period_dateNotification(notif)
        template ='client/notifications.html'  
        client = ClientInfo.objects.get(id = param)
        context = {
        'notif': notif,
        'client':client
             }
        return render(request, template, context)
    else:
        return HttpResponseRedirect(reverse('404'))

def updatesettings(request,id):
    checked = request.POST.get('switch-meter', False)    
    return HttpResponseRedirect(reverse('index'))  
    

def getmeter(request):
    id = request.GET.get('id')
    realtimeRecord = RealTimeBill.objects.filter(meterid_id = id, timestamp = datetime.date.today()).first()
    realtime = realtimeRecord.totalconsumption
    currentread = round(realtimeRecord.currentread,2)
    # Return a JSON response of the data
    return JsonResponse({'dateread': str((datetime.datetime.today())),'total':str(realtime), 'currentread':str(currentread),'amount': 'Php ' +  str(pricing(realtimeRecord.totalconsumption/1000))})

def getnotif(request):
    id = request.GET.get('id')
    data = Notifications.objects.filter(meterid_id = id).order_by('-timestamp', 'isseen').all().values()[:10]
    for d in data:
        d['period']= setTimeNotifications(d.get('timestamp'))
    notif = json.dumps(list(data), default=str)
    # Return a JSON response of the data
    return JsonResponse(notif,safe = False)



def pricing(consumed):
    pricetable =  Pricing.objects.all()
    price =0
    baseprice = 0
    minconsumed = 0
    excess = 0
    for rate in pricetable:
        if rate.isflatrate:
                    baseprice = rate.residentialrate
                    minconsumed = rate.rangeto   
        else:
            if rate.rangefrom <= consumed and rate.rangeto >= consumed: 
                excess = consumed - minconsumed

    price = baseprice + (excess * rate.residentialrate)                
    return round(price,2)

def logoutclient(request):
    from django.contrib.auth import logout
    logout(request)

def notfound(request):
    template = loader.get_template('404.html')
    context = None
    return HttpResponse(template.render(context,request))

def period_dateNotification(notifdata):
    
    for r in notifdata:
        r.period = setTimeNotifications(r.timestamp)
    

