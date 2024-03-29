from django.shortcuts import render,HttpResponse,redirect
from django.contrib.auth.models import User
from django.views.generic import View
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages

# to activate user account
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.urls import NoReverseMatch,reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes,force_str,DjangoUnicodeDecodeError

# import django
# from django.utils.encoding import force_str
# django.utils.encoding.force_text = force_str

# getting token from utils.py
from .utils import TokenGenerator,generate_token

# Emails
from django.core.mail import send_mail,EmailMultiAlternatives
from django.core.mail import BadHeaderError,send_mail
from django.core import mail
from django.conf import settings
from django.core.mail import EmailMessage

# Threadings
import threading

#Reset Password Generators
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailThread(threading.Thread):
    def __init__(self,email_message):
        self.email_message = email_message
        threading.Thread.__init__(self)
    def run(self):
        self.email_message.send()

def Signup(request):
    if request.method == "POST": # if request method and name=email,name-pass1 and name=pass2 in html fields it proccess it here
        email = request.POST['email']
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']
        if password != confirm_password:   # if pass1 and pass2 is not match then through error message above signup form
            messages.warning(request,"Passwrod Is Not Matching")
            return render(request,'Auth/signup.html')
        
        try: # you can't handle the error with if else condition. that time use try exept block (0divison error)
            if User.objects.get(username=email): # if user name is already exist in database
                messages.warning(request,"Email already Taken")
                return render(request,'Auth/signup.html')
    
        except Exception as identifier: # it will not present username in database
            pass
        
        user = User.objects.create_user(email,email,password) # it create user in database User model
        user.is_active = False # superuser False
        user.save()   # it save user
        current_site = get_current_site(request)
        email_subject = "Activate Your Account"
        message = render_to_string('Auth/activate.html',{
            'user': user,
            'domain':'http://127.0.0.1:8000/',
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':generate_token.make_token(user)
        })

        email_message = EmailMessage(email_subject,message,settings.EMAIL_HOST_USER,[email],)
        EmailThread(email_message).start()
        messages.info(request,"Activate Your Account By Clicking Link on your Email")
        return redirect("/login/")
    
    else:
        return render(request,'Auth/signup.html')



class ActivateAccountView(View):
    def get(self,request,uidb64,token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
        except Exception as identifier:
            user = None

        if user is not None and generate_token.check_token(user,token):
            user.is_active = True
            user.save() 
            messages.info(request,"Account Activated Successfully")
            return redirect("/login")
        return render(request,'Auth/activatefail.html')

def handleLogin(request):
    if request.method == "POST":
        username = request.POST['email']
        userpassword = request.POST['pass1']
        myuser = authenticate(username=username,password=userpassword)

        if myuser is not None:
            login(request,myuser)
            messages.success(request,'Login Success')
            return redirect('/CMS/')
        else:
            messages.error(request,"Invalid Credentials")
            return redirect("/login/")
        
    return render(request,'Auth/login.html')


def handleLogout(request):
    logout(request)
    messages.success(request,"Logout Successfull")
    return redirect("/login/")

class RequestResetEmailView(View):
    def get(self,request):
        return render(request,'Auth/request-reset-email.html')
    
    def post(self,request):
        email = request.POST['email']
        user = User.objects.filter(email=email)

        if user.exists():
            current_site = get_current_site(request)
            email_subject = '[Reset Your Password]'
            message = render_to_string('Auth/reset-user-password.html',{
            'domain':'http://127.0.0.1:8000',
            'uid':urlsafe_base64_encode(force_bytes(user[0].pk)),
            'token':PasswordResetTokenGenerator().make_token(user[0])
        })
            
            email_message = EmailMessage(email_subject,message,settings.EMAIL_HOST_USER,[email],)
            EmailThread(email_message).start()
            messages.info(request,"We Have Sent You an Email With Instruction On How to reset the password")
            return render(request,'Auth/request-reset-email.html')
        


class SetNewPasswordView(View):
    def get(self,request,uidb64,token):
        context = {
            'uidb64':uidb64,
            'token':token
        }
        try:
            user_id = force_bytes(urlsafe_base64_decode(uidb64))
            user=User.objects.get(pk=user_id)

            if not PasswordResetTokenGenerator().check_token(user,token):
                messages.warning(request,"Password Reset Link Is Invalid")
                return render(request,'Auth/request-reset-email.html')
            
        except DjangoUnicodeDecodeError as identifier:
            pass

        return render(request,'Auth/set-new-password.html',context)
    

    def post(self,request,uidb64,token):
        context={
            'uidb64':uidb64,
            'token':token
        }
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']
        if password != confirm_password:
            messages.warning(request,"Passwrod Is Not Matching")
            return render(request,'Auth/set-new-password.html',context)
        
        try:
            user_id=force_bytes(urlsafe_base64_decode(uidb64))
            user=User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            messages.success(request,'Password Reset Success Please Login with new Password')
            return redirect('/login/')
        
        except DjangoUnicodeDecodeError as identifier:
            messages.error(request,"something went wrong")
            return render(request,'Auth/set-new-password.html',context)
        

