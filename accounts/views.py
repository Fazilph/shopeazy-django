from django.shortcuts import render,redirect
from .forms import RegistrationForm
from .models import Account
from django.contrib import messages
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
#verifiaction Email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode ,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.models import Cart,CartItem
from carts.views import _cart_id
import requests
# Create your views here.

def register(request):
    if request.method == 'POST':
        form=RegistrationForm(request.POST)
        if form.is_valid():
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            email=form.cleaned_data['email']
            phone_number=form.cleaned_data['phone_number']
            password=form.cleaned_data['password']
            username=email.split('@')[0]
            user=Account.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
            user.phone_number=phone_number
            user.save()
            #user activation
            current_site=get_current_site(request)
            mail_subject='Please Activate Your Account'
            message=render_to_string('accounts/account_verification_email.html',{
            'user' : user ,
            'domain' : current_site,
            'uid' : urlsafe_base64_encode(force_bytes(user.pk))  ,
            'token' : default_token_generator.make_token(user),
            })

            to_email=email
            send_email=EmailMessage(mail_subject , message ,to=[to_email])
            send_email.send()

            # messages.success(request ,'Thank you for registering , we have sent an email ,please verify the email to activate your your account.')
            return redirect ('/accounts/login/?command=verifiaction&email='+email)
    else:
        form=RegistrationForm()

    context={
    'form':form
    }
    return render(request,'accounts/register.html',context)

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart=Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exist=CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exist:
                    cart_item= CartItem.objects.filter(cart=cart)
                    product_variation=[]
                    for item in cart_item:
                        variation=item.variations.all()
                        product_variation.append(list(variation))

                    #get variation from user to get his variations
                    cart_item=CartItem.objects.filter(user=user)
                    ex_var_list=[]
                    id=[]
                    for item in cart_item:
                        existing_variation=item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index=ex_var_list.index(pr)
                            item_id=id[index]
                            item=CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user=user
                            item.save()

                        else:
                            cart_item=CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user=user
                                item.save()



            except:
                pass
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            url=request.META.get('HTTP_REFERER')
            #this url will store the entire previous url :http://127.0.0.1:8000/accounts/login/?next=/cart/checkout/
            try:
                query=requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params=dict(x.split('=') for x in query.split('&'))
                #{'next': '/cart/checkout/'}
                if 'next' in params:
                    next_page=params['next']
                    return redirect(next_page)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request,'accounts/login.html')

@login_required(login_url ='login')
def logout(request):
    auth.logout(request)
    messages.success(request ,'You are logged out')
    return redirect('login')

def activate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user ,token):
        user.is_active=True
        user.save()
        messages.success(request, 'Congratulation your account has been activated!')
        return redirect('login')
    else:
        messages.error(request,'Invalid activation link')

        return redirect('register')

@login_required(login_url ='login')
def dashboard(request):
    return render(request,'accounts/dashboard.html')

def forgetPassword(request):
    if request.method == 'POST':
        email=request.POST['email']
        if Account.objects.filter(email=email).exists():
            user=Account.objects.get(email__exact=email)

            #reset password mail
            current_site=get_current_site(request)
            mail_subject= 'Forgot Password'
            message= render_to_string('accounts/forgotPassword_email.html',{
            'user' : user,
            'domain' : current_site,
            'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
            'token' : default_token_generator.make_token(user),
            })
            to_email=email
            send_email=EmailMessage(mail_subject ,message ,to=[to_email])
            send_email.send()
            messages.success(request,'Password reset email has been sent to your email address')
            return redirect('login')
        else:
            messages.error(request,'Invalid email address')
            return redirect(forgetPassword)

    return render(request,'accounts/forgetPassword_first.html')

def resetpassword_validate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] = uid
        messages.success(request,'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request,'This link has been expired ')
        return redirect('login')
def resetPassword(request):
    if request.method == 'POST':
        password=request.POST['create_password']
        confirm_password=request.POST['confirm_password']
        if password == confirm_password :
            uid = request.session.get('uid')
            user=Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Password reset successfull!')
            return redirect('home')
        else:
            messages.error(request,'Password does not match ')
            return redirect('resetPassword')
    else:
        return render(request,'accounts/resetPassword.html')
