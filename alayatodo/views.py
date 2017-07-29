import json
import collections
from alayatodo import app
from flask_paginate import Pagination, get_page_args
from flask import (
    g,
    redirect,
    render_template,
    request,
    session,
    flash
    )
from alayatodo import models
from models import User, Todo

@app.route('/')
def home():
    with app.open_resource('../README.md', mode='r') as f:
        readme = "".join(l.decode('utf-8') for l in f)
        return render_template('index.html', readme=readme)


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_POST():
    username = request.form.get('username')
    password = request.form.get('password')

    ses = models.loadSession()
    user = ses.query(User).filter(User.username==username).filter(User.password==password).all()
    if user:
        session['user'] = {'username':user[0].username, 'password':user[0].password, 'id':user[0].id}
        session['logged_in'] = True
        return redirect('/todo')

    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user', None)
    return redirect('/login')


@app.route('/todo/<id>', methods=['GET'])
def todo(id):
    if not session.get('logged_in'):
        return redirect('/login')
    """
    User cannot see individual todo from ther user.
    If an attempt is made to view '/todo/<id>' belongning to another
    user, they are brought back to '/todo' with a flash message.
    """
    ses = models.loadSession()
    todo = ses.query(Todo).filter(Todo.id==id).filter(Todo.user_id==session['user']['id']).order_by(Todo.id).all()
    if todo:
        return render_template('todo.html', todo=todo[0])
    else:
        flash('Cannot view tasks from other users')
        return redirect('/todo')


@app.route('/todo',  defaults={'page': 1}, methods=['GET'])
@app.route('/todo/', defaults={'page': 1}, methods=['GET'])
@app.route('/todo/page/<int:page>',  methods=['GET'])
@app.route('/todo/page/<int:page>/', methods=['GET'])
def todos(page):
    if not session.get('logged_in'):
        return redirect('/login')
    # User cannot see todo lists from other user
    ses = models.loadSession()
    todos = ses.query(Todo).filter(Todo.user_id==session['user']['id']).order_by(Todo.id).all()

    total = len(todos)
    page, per_page, offset = get_page_args()
    # Reset per_page and offset values
    per_page = 3
    offset = (page - 1) * per_page
    pagination = Pagination(page=page,
                            per_page=per_page,
                            total=total,
                            record_name='todos',
                            format_total=True,
                            format_number=True,
                            css_framework='bootstrap3',
                            )

    """
    Number of elements of todos is limited to per_page value.
    Render elements starting at the index with offset value.
    """
    return render_template('todos.html', todos=todos[offset:offset+per_page],
                           pagination=pagination, page=page, per_page=per_page)


@app.route('/todo',  methods=['POST'])
@app.route('/todo/', methods=['POST'])
def todos_POST():
    if not session.get('logged_in'):
        return redirect('/login')
    if request.form.get('description', '') != '':
        ses = models.loadSession()
        # new tasks added with incomplete status by default
        ses.add(Todo(user_id = session['user']['id'], description = request.form.get('description', ''), completed_status = 0))
        ses.commit()
        message_str = 'Task \"' + request.form.get('description', '') + '\" has been successfully added.'
    else:
        message_str= 'You must enter a description in order to add a task.'
    flash(message_str)
    return redirect('/todo')

"""
Actions of deleting an element or changing its status
are built within the same function. Each action is selected
using the settings option.
"""
@app.route('/todo', methods=['POST'])
@app.route('/todo/<id>', methods=['POST'])
def todo_modify(id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    ses = models.loadSession()
    task = ses.query(Todo).filter(Todo.id==id).all()[0]
    # Change status to complete or incomplete
    if request.args.get('settings') == 'change_status':
        # Change status from incomplete to complete
        if task.completed_status == 0:
            todo = ses.query(Todo).filter(Todo.id==id).all()[0]
            todo.completed_status=1
            ses.commit()
            message_str = 'Status of task \"' + task.description + '\" has been set to complete.'
        # Change status from complete to incomplete
        elif task.completed_status == 1:
            todo = ses.query(Todo).filter(Todo.id==id).all()[0]
            todo.completed_status=0
            ses.commit()
            message_str = 'Status of task \"' + task.description + '\" has been set to incomplete.'
    # Delete an element
    elif request.args.get('settings') == 'delete':
        ses.delete(ses.query(Todo).filter(Todo.id==id).all()[0])
        ses.commit()
        message_str = 'Task \"' + task.description + '\" has been successfully removed.'
    flash(message_str)
    return redirect('/todo')

@app.route('/todo/<id>/json', methods=['GET'])
def view_json(id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    ses = models.loadSession()
    todo = ses.query(Todo).filter(Todo.id==id).all()[0]
    data = collections.OrderedDict([('id',todo.id), ('user_id',todo.user_id), ('description',todo.description), ('completed_status', todo.completed_status)])
    json_todo = json.dumps(data)
    return render_template('json.html', json_todo=json_todo)
