#Autor: Petar Radicevic

# -*- coding: UTF-8 -*-

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import datetime

from sqlalchemy import desc, or_

from kavijar.auth import login_required, check_ban
from kavijar.models import User, Mailmsg
from . import db

bp = Blueprint('mail', __name__, url_prefix='/mail')


@bp.route('/', methods=('GET', 'POST'))
@login_required
@check_ban
def msg_main():
    g.user.statusUpdate = 0
    db.session.commit()
    uid = g.user.idUser
    msg_list = Mailmsg.query.filter(or_(Mailmsg.idTo == uid, Mailmsg.idFrom == uid)) \
        .order_by(desc(Mailmsg.time)).all()
    return render_template('mail/mail.html', msg_list=msg_list)


def send_msg_function(sender, recipient, msgbody, msgtime):
    recipient.statusUpdate += 1
    new_message = Mailmsg(idFrom=sender.idUser, idTo=recipient.idUser,
                          time=msgtime, content=msgbody, readFlag=0)
    db.session.add(new_message)
    db.session.commit()


@bp.route('/send_msg', methods=('GET', 'POST'))
@login_required
@check_ban
def send_msg():
    if request.method == 'POST':
        sender = g.user
        recipient = User.query.filter_by(username=request.form['recipient']).first()
        msgbody = request.form['body']
        msgtime = datetime.datetime.now()
        error = None
        if recipient is None:
            error = "Nepostojeći korisnik!"
        elif len(msgbody) > 256 or len(msgbody) == 0:
            error = "Losa duzina poruke!"
        if error is None:
            send_msg_function(sender, recipient, msgbody, msgtime)
        else:
            flash(error)
    return render_template('mail/send_msg.html')


@bp.route('/view_msg/<int:id>')
@login_required
@check_ban
def view_msg(id):
    curr_msg = Mailmsg.query.filter_by(idMail=id).first()
    if curr_msg is not None and curr_msg.idTo != g.user.idUser and curr_msg.idFrom != g.user.idUser:
        curr_msg = None
    if curr_msg is not None and curr_msg.idTo == g.user.idUser:
        curr_msg.readFlag = 1
        db.session.commit()
    return render_template('mail/view_msg.html', curr_msg=curr_msg)
