# coding=utf-8
from flask import *
from flask_cors import CORS

from baiducloudengine import BaiduCloudEngine
import utils
import downloadengine

bdce = BaiduCloudEngine(webserver=True)
pushCommand = '服务器运行中'
domain = '127.0.0.1:8000'
app = Flask(__name__)
CORS(app)

def required_login(func):
    def wrapper(*args, **kwargs):
        global bdce
        if bdce.logined:
            return func(*args, **kwargs)
        return redirect('/', code=302)
    return wrapper

@app.route('/')
def index():
    global bdce

    # 已登录检验
    if bdce.logined:
        return redirect('/disk', code=302)
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    global bdce
    global pushCommand

    username = request.form['username']
    password = request.form['password']

    # 空值检验
    if username == '' or password == '':
        pushCommand = '请输入用户名和密码'
        res = {"success": 0}
        return Response(json.dumps(res), mimetype='application/json')
    else:
        pushCommand = utils.last_msg

    if bdce.login(username, password):
        pushCommand = '服务器运行中'
        res = {'success': 1}
        return Response(json.dumps(res), mimetype='application/json')
    else:
        # 出错
        if bdce.verifycode_img_url is not None:
            res = {"success": -1, "verifycode_img_url": bdce.verifycode_img_url}
            pushCommand = '请输入验证码'
            return Response(json.dumps(res), mimetype='application/json')
        else:
            res = {'success': 0}
            return Response(json.dumps(res), mimetype='application/json')


@app.route('/disk')
@required_login
def disk():
    return render_template('disk_home.html')

@app.route('/pushcommand/', methods=['GET', 'POST', 'OPTIONS'])
def pushcommand():
    return Response('data:%s \n\n' % pushCommand, mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)