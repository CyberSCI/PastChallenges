import sys, os
import datetime
import base64
import random
import secrets
import tempfile
from types import SimpleNamespace
from flask import Flask, request, url_for, session, g, render_template, session, redirect
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from ballotscanner import ballot
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from PIL import Image
from io import BytesIO
from .database import db, Votes, init_database

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.update(
        SECRET_KEY=os.urandom(12),
        SESSION_TYPE='filesystem',
        WTF_CSRF_SECRET_KEY=os.urandom(12),
        SESSION_COOKIE_NAME="BSCANNER_SESS",
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Strict",
        PERMANENT_SESSION_LIFETIME=datetime.timedelta(hours=2).total_seconds(),
        SCANNER_PRECINCT=os.getenv("SCANNER_PRECINCT"),
        SCANNER_SERIAL=os.getenv("SCANNER_SERIAL"),
        ADMIN_ENDPOINT=secrets.token_urlsafe(16),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///ballots.db",
        TESTING_FLAG="TESTING-" + os.getenv("TESTING_FLAG"),
        BALLOTCOUNT_FLAG="BALLOTCOUNT-" + os.getenv("BALLOTCOUNT_FLAG"),

    )
    Session(app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    @app.after_request
    def apply_headers(resp):
        resp.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self';"
        resp.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
        resp.headers['Pragma'] = "no-cache"
        resp.headers['Strict-Transport-Security'] = "max-age=63072000; includeSubDomains"
        
        return resp

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')
    
    @app.route('/scan', methods=['POST'])
    def scan():
        if len(request.files) < 1:
            return {"err":"No ballot image uploaded"}, 400

        data = request.files['ballotimage'].read()
        ballotimage = Image.open(BytesIO(data))
        barcode = ballot.findBarcode(ballotimage)

        if barcode is None:
            return {"err":"The uploaded data is not a valid ballot"}, 400

        ballotcode = barcode.data.decode()
        if '-' not in ballotcode:
            return {"err":"The uploaded data is not a valid ballot"}, 400

        res = ballot.process(ballotcode, app, data)
        if res.code == 0:
            precinct, typecode = ballotcode.split("-")
            for vote in res.votes:
                db.session.add(Votes(ballot=typecode, vote=vote))

            db.session.commit()
            return {"msg": "Accepted"},200
        elif res.code == 1:
            ballotcount = db.session.query(Votes.id).count()
            ballotflag = app.config['BALLOTCOUNT_FLAG']
            return {"msg": f"CURRENT NUMBER OF CAST BALLOTS: {ballotcount}\nSIGNATURE CODE: {ballotflag}"}, 200
        elif res.code == 2:
            counts = db.session.query(
                Votes.vote,
                func.count(Votes.id).label("vote_count")
                ).group_by(Votes.vote).all()

            countmessage = "CURRENT VOTE COUNTS:"
            for vc in counts:
                countmessage += f"\n{vc[0]}: {vc[1]}"
            
            return {"msg": countmessage}, 200
        elif res.code < 300:
            return {"msg": res.message}, res.code
        elif res.code >= 400:
             return {"err": res.message}, res.code
        else:
            return redirect(res.location)


    @app.route('/adm/<endpoint>', methods=['GET'])
    def admin(endpoint):
        if endpoint != app.config['ADMIN_ENDPOINT']:
            return '', 404
        else:
            counts = db.session.query(
                Votes.vote,
                func.count(Votes.id).label("vote_count")
                ).group_by(Votes.vote).order_by(text('vote_count desc')).all()

            return render_template(
                'admin.html',
                precinct=app.config['SCANNER_PRECINCT'],
                machineid=app.config['SCANNER_SERIAL'],
                votes=counts
                )

    def uncaught(exType, exVal, exTrace):
        app.logger.error(f"Unhandled Execption: {exType}", exc_info=(exType, exVal, exTrace))

    sys.excepthook = uncaught

    app.wsgi_app = ProxyFix(app.wsgi_app)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


