from flask import Flask, request, render_template
from .config import CONFIG

app = Flask(__name__)


@app.route('/')
@app.route('/planning')
def planning():
    return render_template('index.html', app=CONFIG, planning="active")


@app.route('/simulation')
def simulation():
    return render_template('index.html', app=CONFIG, simulation="active")


@app.route('/plans', methods=['GET', 'POST'])
def plans():
    if request.method == 'GET':
        pass
    else: # post
        pass


@app.route('/plan/<int:plan_id>', methods=['GET', 'PUT', 'DELETE'])
def plan(plan_id):
    if request.method == 'GET':
        pass
    elif request.method == 'PUT':
        pass
    else: # delete
        pass


@app.route('/generators', methods=['GET', 'POST'])
def generators():
    if request.method == 'GET':
        pass
    else: # post
        pass


@app.route('/generators/<int:generator_id>', methods=['GET', 'PUT', 'DELETE'])
def generator(generator_id):
    if request.method == 'GET':
        pass
    elif request.method == 'PUT':
        pass
    else: # delete
        pass
