"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : Game System -- pvp
"""
from . import game, views
from flask_login import current_user
from flask import request, Response
from bson import ObjectId
from app.MongoFunction import db
from .. import socketio, bg_task,client
from flask_socketio import emit, join_room, leave_room, rooms
import json
from time import time
from pprint import  pprint
from app import answer_buffer, QUESTION_NUM
from app.MongoFunction import get_list_of_levels


type_num = {"1 vs 1":2,
            "2 vs 2":4,
            "Battlegrounds":3}


def getNotFull():
    r = []
    for k,v  in type_num.items():
        r.append({"type":k,"player."+str(v):{"$exists":True}})
    return r


# background green thread
def bg_update_room(course):
    while True:
        socketio.sleep(1)
        # cur = db.rooms.find({"course": course,"game_start":{"$exists":False}})
        cur = db.rooms.find({"course": course})
        data = json.dumps(list(cur), default=str)
        socketio.emit('update_room',
                      data,
                      room=course,
                      namespace='/pvp',
                      broadcast = 1,
                      skip_sid=1)
        query = []
        for k,v in type_num.items():
            query.append({"type":k,"player":{"$size":v},"start_game":{"$exists":False}})
        cur = list(db.rooms.find({"$or": query}))
        for r in cur:
            db.rooms.update({"_id": r["_id"]},
                            {"$set": {"start_game": True}})


# background green thread
def bg_full_check():
    print(f"\nbg_full_check started \n")
    while True:
        socketio.sleep(1)
        query = []
        for k, v in type_num.items():
            query.append({"type": k, "player": {"$size": v }} )
        cur = db.rooms.find({"game_start":{"$exists":False},"$or":query})
        for r in cur:
            if str(r["_id"]) not in bg_task:
                db.rooms.update_one({"_id":r["_id"]},{"$set":{"game_start":True}})
                bg_task[str(r["_id"])] = socketio.start_background_task(bg_gaming_thread, str(r["_id"]))


# background green thread
def bg_gaming_thread(room_id):
    start_time = time()
    print(f"\nbg_gaming_thread started {room_id}\n")
    while True:
        socketio.sleep(1.5)
        cur = db.rooms.find_one({"_id": ObjectId(room_id)})
        if cur:
            data = dict(cur)
            if len(data["player"]) ==1 or(room_id in answer_buffer and len(answer_buffer[room_id]) == QUESTION_NUM):
                views.win_game(room_id,data["player"][0])
                # bg_task[room_id] = 0
                return False
            socketio.emit('gaming',
                          json.dumps({"id": room_id,
                           "data":data,
                           "answer":answer_buffer.get(room_id,{})},
                          default=str),
                          room=room_id,
                          namespace='/pvp',
                          broadcast=1,
                          skip_sid=1)
        else:
            cur = db.rooms.find_one({"_id": ObjectId(room_id)})
            if cur:
                data = dict(cur)


@socketio.on('connect', namespace="/pvp")
def on_connect():
    try:
        print("\nconnect to:", request.namespace)
        print(request.args)
        if request.args["course"] in bg_task and bg_task[request.args["course"]] == 0:
            bg_task[request.args["course"]] = socketio.start_background_task(bg_update_room,request.args["course"])
        print("\n")
        return  "server coonnected"
    except Exception as e:
        pprint(e)


@socketio.on('reconnect', namespace='/pvp')
def on_reconnect(data):
    print("\nreconnect to:")
    print(data)
    print(request)
    print("\n")


@socketio.on('join', namespace='/pvp')
def on_join(data):
    try:
        print(f"\n{current_user.get_id()} join to:")
        # check if player is in a started game
        print("query", {"player": {"$in": [current_user.get_id()]}, "game_start": True})
        cur = db.rooms.find_one({"player": {"$in": [current_user.get_id()]}, "game_start": True})
        join = ''
        in_game = 0

        # run thread for the started game
        if cur:
            curL = dict(cur)
            if(len(curL)):
                if str(curL["_id"]) not in bg_task or not bg_task[str(curL["_id"])]:
                    bg_task[str(curL["_id"])] = socketio.start_background_task(bg_gaming_thread,str(curL["_id"]))
                join_room(str(curL["_id"]))
                print(str(curL["_id"]))
                join = curL["_id"]
                in_game = 1

        # join the course pvp room
        if request.args["course"] in bg_task:
            join_room(data["room"])
            print(data["room"])
            join = data["room"]
        print(bg_task)

        # run thread for the course
        if request.args["course"] in bg_task and bg_task[request.args["course"]] == 0:
            bg_task[request.args["course"]] = socketio.start_background_task(bg_update_room, request.args["course"])

        # run thread for full room checking
        if bg_task["bg_full_check"] == 0:
            bg_task["bg_full_check"] = socketio.start_background_task(bg_full_check)

        print({"status":1,"join":join,"rooms":rooms(),"in_game":in_game,"user":current_user.get_id()})
        print("\n")

        return {"status":1,"join":join,"rooms":rooms(),"in_game":in_game,"user":current_user.get_id()}
    except KeyError as e:
        return ""


@socketio.on('disconnect', namespace='/pvp')
def on_disconnect():
    print("pvp Client disconnected")
    on_leave_room()


@socketio.on('message', namespace='/pvp')
def on_message(message):
    print("\n","text",message,"\n")
    return "message was received by server"


@socketio.on('echo', namespace='/pvp')
def on_echo(message):
    print("\n","echo",message,rooms(),"\n")
    return ""
    if "room" in message:
        for r in message["room"]:
            emit("echo",{"data":message["s"],"room":r,"rooms":rooms()}, namespace='/pvp',room=r)
    # elif "change" in message:
    #     cur = db.rooms.watch([])
    #     print("change")
    #     pprint(json.dumps(list(cur),default=str))
        # emit("echo", {"data": message["s"], "rooms": rooms()}, namespace='/pvp', room=request.sid)
    else:
        emit("echo", {"data": message, "rooms": rooms()}, namespace='/pvp',room=request.sid)
    print(bg_task,"\n")
    return ("echo was received by server", rooms())


@socketio.on('new_room', namespace='/pvp')
def on_new_room(data):
    try:
        print("\n\n\n\n","new_room",data,"\n\n\n\n")
        room = {
            "course": data['course'],
            "type": data['type'],
            "player": data["player"]
        }
        result = db.rooms.insert_one(room)
        join_room(str(result.inserted_id))
        return json.dumps({"status": result.acknowledged,
                           "new_room": result.inserted_id,
                           }, default=str)
    except KeyError as e:
        return json.dumps({"status": result.acknowledged,
                           "msg": "KeyError",
                           }, default=str)


@socketio.on('change_room', namespace='/pvp')
def on_change_room(data):
    try:
        # print("\n","change_room",data)
        # print(current_user.get_id())
        with client.start_session() as s:
            s.start_transaction()
            db.rooms.update_many({"player": {"$in": [current_user.get_id()]},"game_start":{"$exists":False}},
                                     {"$pull": {"player": current_user.get_id()}})
            cur = db.rooms.find_one({"_id": ObjectId(data)}, {"type": 1})
            maxnum = type_num[cur["type"]] if cur["type"] in type_num else 1000
            for r in rooms():
                if r != data and r != request.sid and r not in bg_task:
                    leave_room(r)
            db.rooms.delete_many({"player": []})
            # cond = getNotFull()
            cur = db.rooms.update_one({"_id": ObjectId(data),"game_start":{"$exists":False}},
                            {"$push": {"player":
                            {"$each":[current_user.get_id()],
                             "$slice":maxnum}}})
            if cur.modified_count:
                join_room(str(data))
                s.commit_transaction()
            else:
                s.abort_transaction()
        return json.dumps({"status": 1,
                           # "new_room": result.inserted_id,
                           }, default=str)
    except Exception as e:
        print(e)
        return json.dumps({"status": 0,
                           "msg": str(e),
                           }, default=str )


@socketio.on('leave_room', namespace='/pvp')
def on_leave_room():
    try:
        with client.start_session() as s:
            s.start_transaction()
            db.rooms.update_many({"player": {"$in": [current_user.get_id()]},"game_start":{"$exists":False}},
                                     {"$pull": {"player": current_user.get_id()}})
            db.rooms.delete_many({"player": []})
            for r in rooms():
                if r != request.sid and r not in bg_task:
                    leave_room(r)
            s.commit_transaction()
        print("leave_room","\n\n\n")
        return json.dumps({"status":1,}, default=str)
    except KeyError as e:
        return json.dumps({"status": 0,"msg": "KeyError"})

# @game.route('/leave_room', methods=['POST'])
# def on_leave_room():
#     try:
#         with client.start_session() as s:
#             s.start_transaction()
#             db.rooms.update({"player": {"$in": [current_user.get_id()]}},
#                                      {"$pull": {"player": current_user.get_id()}})
#             db.rooms.delete_many({"player": []})
#             for r in rooms():
#                 if r != request.headers["sid"] and r not in bg_task:
#                     leave_room(r)
#             result = s.commit_transaction()
#         print(result,dir(result),"\n\n\n")
#         return Response(json.dumps({"status":1,
#                                     }, default=str), mimetype='application/json')
#     except KeyError as e:
#         return Response(json.dumps({"status": 0,
#                                     "msg": "KeyError",
#                                     }, default=str), mimetype='application/json')


@socketio.on('update_focus', namespace='/pvp')
def on_update_focus(data):
    try:
        # print("\n","on_update_focus")
        # print(current_user.get_id())
        # print(data['focus'])
        if data:
            socketio.emit("position", {"user": current_user.get_id(),
                "focus": data["focus"]},
                 room=data['room'],
                 namespace='/pvp',
                 broadcast=1,
                 skip_sid=request.sid,
                 include_self=False)
        # print("\n")
        return {}
    except Exception as e:
        print(e)
        return json.dumps({"status": 0,
                           "msg": str(e),
                           }, default=str)


@game.route('/get_rooms', methods=['GET'])
def get_rooms():
    cur = db.rooms.find({"course":request.args["course"]})
    return Response(json.dumps(list(cur), default=str), mimetype='application/json')


@socketio.on('connect', namespace="/chat")
def on_connect_chat():
    try:
        print("connect to connect_chat:", request.namespace)
        print("\n")
        user = db.users.find_one({'username': current_user.username})
        user_id = user['_id']
        if 'avatar' in user.keys():
            user_avatar = user['avatar']
        else:
            user_avatar = None
        course_code = request.args['course']
        course_id = db.courses.find_one({"code": course_code})['_id']
        if get_list_of_levels(user_id, course_id)['levels']:
            level = get_list_of_levels(user_id, course_id)['levels'][0]
        else:
            level = None
        data = {"name": current_user.username, "level": level['level'], "avatar": user_avatar}
        data = json.dumps(data)
        socketio.emit("chat_message", data,
                      namespace='/chat',
                      broadcast=1, )
        return "server coonnected"
    except Exception as e:
        pprint(e)


@socketio.on('broadcast_chat', namespace="/chat")
def on_broadcast_chat(data):
    try:
        print("\nconnect to:", request.namespace)
        socketio.emit("chat_message", data,
                      namespace='/chat',
                      broadcast=1,)
        print("\n")
        return "server broadcast_chat"
    except Exception as e:
        pprint(e)
