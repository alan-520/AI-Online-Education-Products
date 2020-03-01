"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : Knowledge System
"""
from flask import Blueprint

knowledge_structure = Blueprint('knowledge_structure', __name__)

from . import views
