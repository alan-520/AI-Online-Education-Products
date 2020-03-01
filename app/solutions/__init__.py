"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : Solution System
"""
from flask import Blueprint

solutionss = Blueprint('solutionss', __name__)

from . import views
