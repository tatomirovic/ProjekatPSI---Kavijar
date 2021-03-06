#Autor: Nikola Tatomirovic i Petar Radicevic

# -*- coding: UTF-8 -*-
import functools
import click

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask.cli import with_appcontext
import datetime

from . import db
from .models import User, City
from . import game_rules as gr

bp = Blueprint('auth', __name__, url_prefix='/auth')


# POST FORMULAR ZA LOGIN
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        error = None
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user is None:
            error = 'Pogrešno korisničko ime.'
        elif not check_password_hash(user.password, password):
            error = 'Pogrešna lozinka.'
        elif user.dateUnban is not None:
            if user.dateUnban > datetime.datetime.now():
                error = 'Banovani ste!'
            else:
                user.dateUnban = None
                db.session.commit()
        if error is None:
            session.clear()
            session['user_id'] = user.idUser
            return redirect('/redirect')
        flash(error)

    return render_template('auth/login.html')


# POST FORMULAR ZA REGISTER
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cityname = request.form['cityname']
        error = None
        if not username:
            error = 'Korisničko ime ne sme biti prazno.'
        elif not password:
            error = 'Lozinka ne sme biti prazna.'
        elif User.query.filter_by(username=username).first():
            error = 'Korisnik sa tim imenom već postoji.'

        if error is None:
            new_user = User(username=username, password=generate_password_hash(password), role='I',
                            caviar=0, statusUpdate=0, dateUnban=None, dateCharLift=None)
            db.session.add(new_user)
            db.session.commit()

            idUser = User.query.filter_by(username=username).first().idUser
            gr.createCity(idUser, cityname)

            flash(f"Igrač {username} je uspešno registrovan!")
            return redirect(url_for('auth.login'))
        flash(error)
    return render_template('auth/register.html')


# WRAPPER KOJI OSIGURAVA DA SU SESSION PODACI PRISUTNI PRE SVAKOG REQUESTA
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
        g.city = None
        g.building_upgrade_costs = None
        g.unit_costs = None
    else:
        g.user = User.query.filter_by(idUser=user_id).first()
        if g.user.role == 'I':
            g.city = City.query.filter_by(idOwner=user_id).first()
            g.building_upgrade_costs = gr.building_costs
            g.unit_costs = gr.unit_costs


# LOGOUT METODA
@bp.route('/logout')
def logout():
    click.echo("Usao sam u logout!")
    session.clear()
    return redirect(url_for('auth.login'))


# WRAPPER KOJI ZABRANJUJE BANOVANOM KORISNIKU AKCIJE
def check_ban(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is not None:
            if g.user.dateUnban is not None:
                if g.user.dateUnban > datetime.datetime.now():
                    error = "Banovani ste!"
                    flash(error)
                    session.clear()
                    return redirect(url_for('auth.login'))
                else:
                    g.user.dateUnban = None
                    db.session.commit()
        return view(**kwargs)

    return wrapped_view


# WRAPPER ZA METODE KOJE SU ISKLJUCIVO ZA IGRACE
def player_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user.role != 'I':
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


# OPSTI WRAPPER ZA METODE KOJE SU ZAJEDNICKE SVIM USERIMA
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


# WRAPPER ZA METODE KOJE SU ISKLJUCIVO ZA ADMINE
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif g.user.role != 'A':
            error = "Nemate admin privilegije!"
            flash(error)
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


# WRAPPER ZA METODE KOJE SU ISKLJUCIVO ZA MODOVE
def mod_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif g.user.role != 'M':
            error = "Nemate mod privilegije!"
            flash(error)
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


# DODAVANJE ADMINA PREKO KOMANDNE LINIJE (sintaksa: flask add-admin {user} {password})
def add_admin(username, password):
    if User.query.filter_by(username=username).first() is None:
        new_admin = User(username=username, password=generate_password_hash(password), role='A',
                         caviar=0, statusUpdate=0, dateUnban=None, dateCharLift=None)
        db.session.add(new_admin)
        db.session.commit()
        return f"Admin sa username: {username}, password: {password} je uspešno kreiran"
    else:
        return f"User sa username: {username} već postoji"


# POVEZIVANJE GORNJE METODE SA CLI
@click.command('add-admin')
@click.argument('username')
@click.argument('password')
@with_appcontext
def add_admin_cli(username, password):
    click.echo(add_admin(username,password))

# REGISTROVANJE KOMANDE
def init_app(app):
    app.cli.add_command(add_admin_cli)
