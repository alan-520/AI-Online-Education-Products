"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : GUIDE SYSTEM ROUTES
"""

from flask import Blueprint

guide = Blueprint('guide', __name__)

from . import adminPages