"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : Profile System
"""
from flask import Blueprint

profile = Blueprint('profile', __name__)

from . import views