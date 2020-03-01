"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : Game System
"""
from flask import Blueprint

game = Blueprint('game', __name__)

from . import views, pvp_socket