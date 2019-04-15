# -*- encoding=UTF-8 -*-
from photowall import app, db
from photowall import models as md
from flask import render_template, redirect, request, flash, get_flashed_messages, send_from_directory
import random, hashlib, json
from flask_login import login_user, logout_user, current_user, login_required
import uuid, os
from photowall.qiniusdk import qiniu_upload_file


@app.route('/')
def index():
    images = md.Image.query.order_by(db.desc(md.Image.id)).limit(10).all()
    return render_template('index.html', images=images)


@app.route('/image/<int:image_id>/')
@login_required
def image(image_id):
    image = md.Image.query.get(image_id)
    if image == None:
        return redirect('/')
    return render_template('pageDetail.html', image=image)


@app.route('/profile/<int:user_id>/')
@login_required
def profile(user_id):
    user = md.User.query.get(user_id)
    if user == None:
        return redirect('/')
    paginate = md.Image.query.paginate(page=1, per_page=1, error_out=False)
    return render_template('profile.html', user=user, has_next=paginate.has_next,images=paginate.items)

@app.route('/profile/images/<int:user_id>/<int:page>/<int:per_page>/')
def user_images(user_id, page, per_page):
    paginate = md.Image.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)
    map = {'has_next':paginate.has_next}
    images = []
    for image in paginate.items:
        imgvo = {'id':image.id, 'url':image.url, 'comment_count':len(image.comments) }

        images.append(imgvo)
    map['images'] = images
    return json.dumps(map)

@app.route('/regloginpage/')
def regloginpage():
    msg = ''
    for m in get_flashed_messages(with_categories=False, category_filter=['reglogin']):#参数一参数二
        msg = msg + m
    return render_template('login.html', msg=msg, next=request.values.get('next'))

def redirect_with_msg(target, msg, category):
    if msg !=None:
        flash(msg, category=category)
    return redirect(target)


@app.route('/login/', methods={'post', 'get'})
def login():
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()

    if username =='' or password == '':
        return redirect_with_msg('/regloginpage/', u'用户名或密码不能为空', 'reglogin')

    user = md.User.query.filter_by(username=username).first()
    if user == None:
        return redirect_with_msg('/regloginpage/', u'用户名不存在', 'reglogin')

    m = hashlib.md5()
    m.update((password+user.salt).encode())
    if (m.hexdigest() != user.password):
        return redirect_with_msg('/regloginpage/', u'密码错误', 'reglogin')

    login_user(user)

    next = request.values.get('next')
    if next != None and next.startswith('/') > 0:
        return redirect(next)
    return redirect('/')


@app.route('/reg/', methods={'post','get'})
def reg():
    #request.args
    #request.form
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()

    if username =='' or password == '':
        return redirect_with_msg('/regloginpage/', u'用户名或密码不能为空', 'reglogin')

    user = md.User.query.filter_by(username=username).first()
    if user != None:

        return redirect_with_msg('/regloginpage/', u'用户名已存在', 'reglogin')


    #更多判断

    salt = ''.join(random.sample('0123456789abcdefghijklmnABCDEFGHIJKLMN',6))
    m = hashlib.md5()
    m.update((password+salt).encode())
    password = m.hexdigest()
    user = md.User(username, password, salt)
    db.session.add(user)
    db.session.commit()

    login_user(user)

    next = request.values.get('next')
    if next != None and next.startswith('/') > 0:
        return redirect(next)
    return redirect('/')


@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/')


def save_to_qiniu(file, file_name):
    return qiniu_upload_file(file, file_name)


def save_to_local(file,file_name):
    save_dir = app.config['UPLOAD_DIR']
    file.save(os.path.join(save_dir,file_name))
    return '/image/' + file_name


@app.route('/upload/',methods={'post'})
def upload():
    file = request.files['file']
    file_ext = ''
    if file.filename.find('.')>0:
        file_ext = file.filename.rsplit('.',1)[1].strip().lower()#lower将字符串转化为小写
    if file_ext in app.config['ALLOWED_EXT']:
        file_name = str(uuid.uuid1()).replace('-','') + '.' + file_ext
        url = save_to_local(file,file_name)
        if url != None:
            db.session.add(md.Image(url, current_user.id))
            db.session.commit()


    return redirect('/profile/%d' % current_user.id)


@app.route('/image/<image_name>')
def view_image(image_name):
    return send_from_directory(app.config['UPLOAD_DIR'], image_name)


@app.route('/addcomment/', methods={'post'})
def add_comment():
    image_id = int(request.values['image_id'])
    content = request.values['content']
    comment = md.Comment(content, image_id, current_user.id)
    db.session.add(comment)
    db.session.commit()
    return json.dumps({"code":0, "id":comment.id,
                       "content":comment.content,
                       "username":comment.user.username,
                       "user_id":comment.user_id})