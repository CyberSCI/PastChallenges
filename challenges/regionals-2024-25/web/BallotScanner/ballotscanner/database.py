from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import random
from . import ballot


db = SQLAlchemy()

class Votes(db.Model):
    __tablename__ = "Votes"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, server_default=func.current_timestamp())
    ballot = db.Column(db.String(16), nullable=False)
    vote = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f"<Vote {self.id}:{self.ballot}>"


def init_database(db):
    ballots = list(range(125, 871))
    random.shuffle(ballots)
    for n in range(435):
        selection = random.choice(ballot.SEQUENCE)
        ballotid = ballots[n]
        db.session.add(Votes(ballot=f"000{ballotid}Y", vote=selection))
    
    db.session.commit()
