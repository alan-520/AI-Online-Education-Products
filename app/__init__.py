"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : Town System
"""

from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from app.config import Config
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask import Flask, render_template
from flask_socketio import SocketIO
import pymongo as pm

# mongodb import ----------------
# mongodb+srv://public:1234567890unsw@devdb-30fsv.mongodb.net/test

client = pm.MongoClient("mongodb+srv://public:1234567890unsw@devdb-30fsv.mongodb.net/test?retryWrites=true&w=majority")
db = client.main

# plugins setting ----------------
bootstrap = Bootstrap()
login_manager = LoginManager()
secure = Bcrypt()
mail = Mail()
cors = CORS()

# install package eventlet ----------------
socketio = SocketIO(async_mode="eventlet")
bg_task = {}
answer_buffer = {}
QUESTION_NUM = 10
MCQ_QUESTION_NUM = 4


# factory function
def create_app():
    # config & initial app ----------------
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    secure.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'guide.login'
    bootstrap.init_app(app)
    cors.init_app(app, supports_credentials=True)
    app.jinja_env.globals.update(__builtins__)

    # blueprint register ----------------
    # guide
    from .guide import guide
    app.register_blueprint(guide, url_prefix='/guide')

    # knowledge_structure
    from .knowledge_structure import knowledge_structure
    app.register_blueprint(knowledge_structure, url_prefix='/knowledge_structure')

    # town
    from .town import town
    app.register_blueprint(town, url_prefix='/town')

    # game
    from .game import game
    app.register_blueprint(game, url_prefix='/game')

    # solutions
    from .solutions import solutionss
    app.register_blueprint(solutionss, url_prefix='/solutions')

    # profile
    from .profile import profile
    app.register_blueprint(profile, url_prefix='/profile')

    # previous router ----------------

    # welcome
    @app.route('/')
    def welcome():
        return render_template('/welcome/welcome.html')

    # error page
    @app.errorhandler(404)
    def miss(e):
        return render_template('/error/404.html'), 404

    @app.errorhandler(500)
    def error(e):
        return render_template('/error/500.html'), 500

    # socket io initialize ----------------
    socketio.init_app(app)
    # events for each course namespace
    cur = db.courses.find()
    for doc in cur:
        # bg_task[doc["code"]] = event.Event()
        bg_task[doc["code"]] = 0
    bg_task["bg_full_check"] = 0

    return app