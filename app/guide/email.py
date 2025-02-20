"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : GUIDE SYSTEM -- Send reset password email
"""
from flask_mail import Message
from app import mail
from SevManager import app
from flask import current_app, render_template
from threading import Thread


def send_asunc_mail(apps, msg):
    with apps.app_context():
        mail.send(msg)


def send_reset_password_mail(user, token):
    msg = Message('[Data Hunter Team]Reset your password',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.find_email()],
                  html=render_template('/guide/send_mail.html', user=user, token=token))
    Thread(target=send_asunc_mail, args=(app, msg, )).start()

