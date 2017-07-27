import json
import collections
from alayatodo import app
from flask import (
    g,
    redirect,
    render_template,
    request,
    session,
    flash
    )

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

    sql = "SELECT * FROM users WHERE username = '%s' AND password = '%s'";
    cur = g.db.execute(sql % (username, password))
    user = cur.fetchone()
    if user:
        session['user'] = dict(user)
        session['logged_in'] = True
        return redirect('/todo')

    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user', None)
    return redirect('/')


@app.route('/todo/<id>', methods=['GET'])
def todo(id):
    cur = g.db.execute("SELECT * FROM todos WHERE id ='%s'" % id)
    todo = cur.fetchone()
    return render_template('todo.html', todo=todo)


@app.route('/todo', methods=['GET'])
@app.route('/todo/', methods=['GET'])
def todos():
    if not session.get('logged_in'):
        return redirect('/login')
    cur = g.db.execute("SELECT * FROM todos")
    todos = cur.fetchall()
    return render_template('todos.html', todos=todos)


@app.route('/todo', methods=['POST'])
@app.route('/todo/', methods=['POST'])
def todos_POST():
    if not session.get('logged_in'):
        return redirect('/login')
    if request.form.get('description', '') != '':
        g.db.execute(
            "INSERT INTO todos (user_id, description, completed_status) VALUES ('%s', '%s', '%s')"
            # new tasks added with incomplete status by default
            % (session['user']['id'], request.form.get('description', ''), 0)
            )
        message_str = 'Task \"' + request.form.get('description', '') + '\" has been successfully added.'
    else:
        message_str= 'You must enter a description in order to add a task.'
    g.db.commit()
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
    
    task = g.db.execute("SELECT * FROM todos WHERE id ='%s'" % id).fetchone()
    # Change status to complete or incomplete
    if request.args.get('settings') == 'change_status':
        # Change status from incomplete to complete
        if task[3] == 0:
            g.db.execute("UPDATE todos SET completed_status = 1 WHERE id ='%s'" % id)
            message_str = 'Status of task \"' + task[2] + '\" has been set to complete.'
        # Change status from complete to incomplete
        elif task[3] == 1:
            g.db.execute("UPDATE todos SET completed_status = 0 WHERE id ='%s'" % id)
            message_str = 'Status of task \"' + task[2] + '\" has been set to incomplete.'
    # Delete an element
    elif request.args.get('settings') == 'delete':
        g.db.execute("DELETE FROM todos WHERE id ='%s'" % id)
        message_str = 'Task \"' + task[2] + '\" has been successfully removed.'
    g.db.commit()
    flash(message_str)
    return redirect('/todo')

@app.route('/todo/<id>/json', methods=['GET'])
def view_json(id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    todo = g.db.execute("SELECT * FROM todos WHERE id ='%s'" % id).fetchone()
    data = collections.OrderedDict([('id',todo[0]), ('user_id',todo[1]), ('description',todo[2]), ('status_completed', todo[3])])
    json_todo = json.dumps(data)
    return render_template('json.html', json_todo=json_todo)
