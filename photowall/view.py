# -*- encoding=UTF-8 -*-
from photowall import app, db
from photowall import models as md
from flask import render_template, redirect, request


@app.route('/')
def index():
    images = md.Image.query.order_by(db.desc(md.Image.id)).limit(10).all()
    return render_template('index.html', images=images)


@app.route('/image/<int:image_id>/')
def image(image_id):
    image = md.Image.query.get(image_id)
    if image == None:
        return redirect('/')
    return render_template('pageDetail.html', image = image)


@app.route('/profile/<int:user_id>/')
def profile(user_id):
    user = md.User.query.get(user_id)
    if user == None:
        return redirect('/')
    return render_template('profile.html', user=user)

@app.route('/regloginpage/')
def regloginpage():
    return render_template('login.html')


@app.route('/reg/')
def reg():
    #request.args
    #request.form
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()

    user = md.User.query.filter_by(username=username).first()
    if user != None:
        flash(u'用户名已存在', category=ca)