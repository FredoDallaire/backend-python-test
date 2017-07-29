from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import sqlite3

from flask import Flask, g

engine = create_engine('sqlite:///temp/alayatodo.db', echo=True)
Base = declarative_base(engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(Integer)
    password = Column(Integer)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return "<User(username='%s', password='%s')>" % (self.username, self.password)

class Todo(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    description = Column(String)
    completed_status = Column(Integer)

    def __init__(self, user_id, description, completed_status):
        self.user_id = user_id
        self.description = description
        self.completed_status= completed_status

    def __repr__(self):
        return "<Todo(user_id='%s', description='%s', completed_status='%s')>" % (self.user_id, self.description, self.completed_status)

def loadSession():
    metadata = Base.metadata
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
