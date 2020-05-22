from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, json
)
from werkzeug.exceptions import abort

from kavijar.auth import login_required, player_required, check_ban
from kavijar.auth import login_required
from . import db

from .models import City, Building, User
import functools, datetime
from . import updateWrappers

bp = Blueprint('game', __name__)

@bp.route('/')
@player_required
@check_ban
@updateWrappers.update_resources
def index():
    city_list = City.query.all()
    city_list_json = []
    city_user_names = {}
    firstKey = None
    for city in city_list:
        #print(f'Our city is: {city.serialize()}')
        city_json = city.serialize()
        city_json['ownerName'] = User.query.filter_by(idUser=city.idOwner).first().username
        city_list_json.append(city_json)
    #print(f"The dump is: {json.dumps(city_list_json)}")
    return render_template('game/main_map.html', city_list=city_list_json)

