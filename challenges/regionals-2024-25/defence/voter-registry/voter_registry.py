#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2024/25
#
# Voter Registry Service by 0xd13a

from flask import Flask, render_template, redirect, request, abort, make_response
import sqlite3
import jwt
import sys
import base64
import traceback
from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa
from pyzbar.pyzbar import decode
from PIL import Image
import json
import io

voters = {}
admins = {}
sig_verify = True

DB = "./voter-list.db"

jwt_key = "LXg7GMrjNzIj5XQzgJy2sJVXVweIaoFPKjeMe25Tnjtv9eHkQjISqoJrcrdkJKQ5"

# Set up port to communicate on
server_port = 443
if len(sys.argv) == 2:
    server_port = int(sys.argv[1])

app = Flask(__name__, template_folder=".")

# Person informaton record
class Person:
    id = ""
    name = ""
    dob = ""
    address = ""
    admin = False

    def __init__(self, id, name, dob, address, admin):
        self.id = id
        self.name = name
        self.dob = dob
        self.address = address
        self.admin = admin

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_dob(self):
        return self.dob

    def set_dob(self, dob):
        self.dob = dob

    def get_address(self):
        return self.address

    def set_address(self, address):
        self.address = address

    def is_admin(self):
        return self.admin

    def set_admin(self, admin):
        self.admin = admin

def exec_sql(query, param=[], update=False):
    """ Execute database query """
    con = None
    cur = None
    rows = []
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        for row in cur.execute(query, param):
            rows.append(row)
        if update:
            con.commit()
    except Exception as e:
        print(e)
        traceback.print_exc()
    finally:
        if cur != None:
            cur.close()
        if con != None:
            con.close()
    return rows

def get_error_page(msg):
    """ Output descriptive error page """
    return "<html><body><h2>{}</h2></body></html>".format(msg)

def load_voters():
    """ Load all voter records """
    global voters, admins

    voters = {}
    admins = {}
    rows = exec_sql("SELECT id, name, dob, address, admin FROM voters;", [])
    for row in rows:
        if row[4] == 1:
            admins[row[0]] = Person(row[0], row[1], row[2], row[3], True)
        else:
            voters[row[0]] = Person(row[0], row[1], row[2], row[3], False)

def create_voter(voter: Person):
    """ Create a new voter """
    rows = exec_sql("INSERT INTO voters (id, name, dob, address, admin) VALUES(?, ?, ?, ?, ?);", [voter.get_id(),
            voter.get_name(), voter.get_dob(), voter.get_address(), 0], True)
    load_voters()
    return rows

def update_voter(voter: Person):
    """ Update existing voter record """
    rows = exec_sql("UPDATE voters SET address = ? WHERE id = ?;", [voter.get_address(), voter.get_id()], True)
    load_voters()
    return rows

def get_user(request):
    """ Retrieve currently logged in user. """

    token = request.cookies.get('token')

    if token == None:
        return None
    else:
        try:
            decoded_data = jwt.decode(jwt=token, key=jwt_key, algorithms=["HS256"], options={"verify_signature": sig_verify})
        except Exception as e:
            return None
        if "id" not in decoded_data or "admin" not in decoded_data:
            return None
        user = None
        id = decoded_data["id"]
        if id in voters.keys():
            user = voters[id]
        elif id in admins.keys():
            user = admins[id]
        else:
            return None
        user.set_admin(decoded_data["admin"])
        return user

def set_current_user(response, user):
    """ Set currently logged in user. """

    if user == None:
        response.delete_cookie('token')
    else:
        token = jwt.encode(payload={"id": user.get_id(), "admin": user.is_admin()}, key=jwt_key, algorithm="HS256")
        response.set_cookie('token', token)

@app.route("/admin", methods=['GET'])
def admin():
    """ Display a list of all voters (only available to admins) """
    user = get_user(request)
    if user == None:
        return redirect("/")
    
    if not user.is_admin():
        return redirect("/")

    sorted_voters = list((voters | admins).values())
    sorted_voters.sort(key=lambda x: x.get_name())

    resp = make_response(render_template("admin_template.html", user=user.get_name(), voters = sorted_voters))
    set_current_user(resp, user)
    return resp

@app.route("/voter/<id>", methods=['GET', 'POST'])
def voter(id):
    """ Display voter record and make allow voter to make changes. Only the admin and voter themselves are alowed to do this.  """
    user = get_user(request)
    if user == None:
        return redirect("/")

    if id in voters.keys():
        record = voters[id]
    if id in admins.keys():
        record = admins[id]

    if request.method == 'POST':
        address = request.form.get('address', None)
        if address != None:
            record.set_address(address)
            update_voter(record)
    resp = make_response(render_template("voter_template.html", user=user.get_name(), id=record.get_id(), 
                    name=record.get_name(),  dob=record.get_dob(),  address=record.get_address()))
    set_current_user(resp, user)
    return resp

def init():
    """ Init globals """
    global voters, admins, sig_verify
    voters = {}
    admins = {}
    sig_verify = None

@app.route("/add", methods=['GET', 'POST'])
def add():
    """ Add a new voter (only admins are allowed to do this) """
    user = get_user(request)
    if user == None:
        return redirect("/")
    
    if not user.is_admin():
        return redirect("/")
    
    if request.method == 'POST':
        id = request.form.get('id', None)
        name = request.form.get('name', None)
        dob = request.form.get('dob', None)
        address = request.form.get('address', None)
        record = Person(id, name, dob, address, False)
        create_voter(record)
        resp = make_response(redirect("/admin"))
    else:    
        resp = make_response(render_template("add_template.html", user=user.get_name()))

    set_current_user(resp, user)
    return resp

def parse_qr_code(data):
    """ Parse QR code available at sign-in """
    
    try:        
        decodeQR = decode(Image.open(io.BytesIO(data)))
        payload_str = decodeQR[0].data.decode('ascii')
        payload = json.loads(payload_str)
    except:
        return None

    if "id" not in payload or "sig" not in payload:
        return None

    signature = None
    try:
        signature = base64.b64decode(payload["sig"])
    except:
        return None

    # This is a good enough verification for now
    if len(signature) != 64:
        return None

    return payload["id"]

@app.route("/", methods=['GET','POST'])
def login():
    """ Main login handler. """
    load_voters()

    user = get_user(request)
    
    if user == None:
        if request.method == 'GET':
            return render_template("login_template.html")
            
        if 'qr' not in request.files:
            abort(400)

        uploaded_file = request.files['qr']
        data = uploaded_file.read()

        id = parse_qr_code(data)
        if id is None:
            return get_error_page("Invalid QR code!"), 401

        if id in voters.keys():
            user = voters[id]
            resp = make_response(redirect("/voter/{}".format(id)))
            set_current_user(resp, user)
            return resp

        if id in admins.keys():
            user = admins[id]
            resp = make_response(redirect("/admin"))
            set_current_user(resp, user)
            return resp

        return get_error_page("Unknown user!"), 401
    else:
        # Log out
        resp = make_response(render_template("login_template.html"))
        set_current_user(resp, None)
        return resp

if __name__ == '__main__':
    init()
    app.run(host='0.0.0.0', port=server_port, ssl_context='adhoc')
