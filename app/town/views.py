from flask import render_template, abort
from flask_login import login_required,current_user
from app.MongoFunction import *
from . import town


@town.route('/<course>')
@login_required
def entry_town(course):
    if course:
        user = db.users.find_one({'username': current_user.username})
        user_id = user['_id']
        if 'avatar' in user.keys():
            user_avatar = user['avatar']
        else:
            user_avatar = None
        course = db.courses.find_one({'code': course})
        print(course)
        print('------------------')
        code = course['code']
        name = course['name']
        course_id = course['_id']
        chapters = db.chapters.find({'course': course_id})
        get_node = db.knowledge_nodes.find
        if get_list_of_levels(user_id, course_id)['levels']:
            level = get_list_of_levels(user_id, course_id)['levels'][0]
        else:
            level = None

        return render_template('/town/my_town.html',  username=current_user.username, level=level, course=course,
                               is_town=True, code=code, _id=course_id, name=name, chapters=list(chapters),
                               get_node=get_node, avatar=user_avatar)
    else:
        abort(404)
