# coding=utf-8
from flask import *
from flask_cors import CORS
import re
from functools import wraps

from baiducloudengine import BaiduCloudEngine
import utils
import downloadengine

bdce = BaiduCloudEngine(webserver=True)
pushCommand = '服务器运行中'
domain = '127.0.0.1:8000'
app = Flask(__name__)
CORS(app)

def required_login(func):
    @wraps(func)
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
            pushCommand = utils.last_msg
            res = {'success': 0}
            return Response(json.dumps(res), mimetype='application/json')


@app.route('/disk', methods=['GET', 'POST'])
@required_login
def disk():
    global bdce
    global pushCommand

    if request.method == 'GET':
        file = request.args.get('file', '').encode('utf-8')

        return_file = ['/']
        if file != '':
            return_file = re.split('/', file)
            return_file[0] = '/'

        return render_template('disk_home.html', file=json.dumps(return_file))
    elif request.method == 'POST':
        request_file = request.form['file'].encode('utf-8')

        # 检测是否已经拉取过file_list
        try:
            result = bdce.file_list[request_file]
            existed = True
        except Exception:
            result = bdce.get_list(request_file)
            existed = False

        if result != False:
            # 分析json
            file_list = []

            for file in bdce.file_list[request_file]:
                if existed:
                    file_name = file['server_filename']
                    path = file['path']
                else:
                    file_name = eval('u\'' + file['server_filename'] + '\'')
                    path = eval('u\'' + file['path'] + '\'.replace(\'\\\\\',\'\')')

                    file['server_filename'] = file_name
                    file['path'] = path

                file_name = file_name.encode('utf-8')
                path = path.encode('utf-8')

                isdir = file['isdir']

                file_list.append({
                    'href': 'disk?file=%s' % path if isdir == 1 else 'download?file=%s&name=%s' % (path, file_name),
                    'name': file_name
                })

            return_json = {'success': 1, 'file_list': file_list}
            return Response(json.dumps(return_json), mimetype='application/json')
        else:
            # 错误
            pushCommand = utils.last_msg
            res = {'success': 0}
            return Response(json.dumps(res), mimetype='application/json')

@app.route('/download', methods=['GET', 'POST'])
@required_login
def download():
    global bdce
    global pushCommand

    if request.method == 'GET':
        file = request.args.get('file', '').encode('utf-8')
        name = request.args.get('name', '').encode('utf-8')

        if file == '' or name == '':
            return redirect('/disk', code=302)

        return_file = re.split('/', file)
        return_file[0] = '/'

        # 检测文件是否存在
        _file = ''
        for x in return_file:
            if x == name:
                break
            _file += x

        file = bdce.check_file(_file, name.decode('utf-8'))

        if file != False:
            return render_template('download_page.html', file=json.dumps(return_file), file_info=file)
        else:
            return redirect('/disk', code=302)

    elif request.method == 'POST':
        pass

@app.route('/pushcommand/')
def pushcommand():
    return Response('data:%s \n\n' % pushCommand, mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)