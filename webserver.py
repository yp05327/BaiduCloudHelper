# coding=utf-8
from flask import *
from flask_cors import CORS
from functools import wraps

import sys

from baiducloudengine import BaiduCloudEngine
from downloadengine import DownloadEngine
import utils

bdce = BaiduCloudEngine(webserver=True)
# 注意直链连接最大连接数为120
de = DownloadEngine(bdce, thread_num=120, webserver=True)

pushCommand = '服务器运行中'
tmp_lastmsg = ''
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

@app.route('/', methods=['GET'])
def index():
    global bdce

    # 已登录检验
    if bdce.logined:
        return redirect('/disk', code=302)

    return render_template('index.html', logined=bdce.logined)

@app.route('/login', methods=['POST'])
def login():
    global bdce
    global pushCommand

    username = request.form['username']
    password = request.form['password']
    verify = request.form['verify']

    # 空值检验
    if username == '' or password == '':
        pushCommand = '请输入用户名和密码'
        res = {'success': 0, 'error_msg': '请输入用户名和密码'}
        return Response(json.dumps(res), mimetype='application/json')
    else:
        pushCommand = utils.last_msg

    bdce.verifycode = verify.encode('utf-8')

    if bdce.login(username, password, verify):
        pushCommand = '服务器运行中'
        res = {'success': 1}
        return Response(json.dumps(res), mimetype='application/json')
    else:
        # 出错
        if bdce.verifycode_img_url != '':
            res = {'success': -1, 'error_msg': '请输入验证码', 'verifycode_img_url': bdce.verifycode_img_url}
            pushCommand = '请输入验证码'
            return Response(json.dumps(res), mimetype='application/json')
        else:
            pushCommand = utils.last_msg
            res = {'success': 0, 'error_msg': 'See the console.'}
            return Response(json.dumps(res), mimetype='application/json')

@app.route('/logout', methods=['GET'])
def logout():
    global bdce

    bdce.logout()

    return redirect('/', code=302)

@app.route('/disk', methods=['GET', 'POST'])
@required_login
def disk():
    global bdce
    global pushCommand

    if request.method == 'GET':
        file = request.args.get('file', '').encode('utf-8')

        return_file = ['']
        if file != '':
            return_file = file.replace('/', '//').split('/')
            while '' in return_file:
                del (return_file[return_file.index('')])

            return_file.insert(0, '')

        return render_template('disk_home.html', file=json.dumps(return_file), logined=bdce.logined)
    elif request.method == 'POST':
        request_file = request.form['file'].encode('utf-8')

        # 检测是否已经拉取过file_list
        try:
            result = bdce.file_list[request_file]
        except Exception:
            result = bdce.get_list(request_file)

        if result != False:
            # 分析json
            file_list = []

            for file in bdce.file_list[request_file]:
                file_name = file['server_filename'] .encode('utf-8')
                path = file['path'].encode('utf-8')

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
            res = {'success': 0, 'error_msg': 'See the console.'}
            return Response(json.dumps(res), mimetype='application/json')

@app.route('/download', methods=['GET'])
@required_login
def download():
    global bdce
    global pushCommand

    file = request.args.get('file', '').encode('utf-8')
    name = request.args.get('name', '').encode('utf-8')

    if file == '' or name == '':
        return redirect('/disk', code=302)

    return_file = file.replace('/', '//').split('/')
    while '' in return_file:
        del (return_file[return_file.index('')])

    return_file.insert(0, '')

    # 检测文件是否存在
    _file = file.replace('/' + name , '')

    download_file = (_file + '/' + name).decode('utf-8')

    if _file == '':
        _file = '/'

    file = bdce.check_file(_file, name.decode('utf-8'))

    if file != False:
        return render_template('download_page.html', file=json.dumps(return_file), download_file= download_file, file_info=file, logined=bdce.logined)
    else:
        pushCommand = utils.last_msg
        return redirect('/disk', code=302)


@app.route('/task', methods=['GET', 'POST'])
@required_login
def task():
    global bdce
    global pushCommand

    if request.method == 'GET':
        # 读取任务
        _task = []
        for task in de.task_list:
            _task.append({'name': task.name, 'size': task.size, 'save_file': task.save_file, 'ranges': task.ranges, 'download_status': task.download_status})

        return render_template('task.html', task=json.dumps(_task), logined=bdce.logined)

    elif request.method == 'POST':
        action = request.form['action'].encode('utf-8')

        if action == 'add':
            file = request.form['file'].encode('utf-8')
            name = request.form['name'].encode('utf-8')
            save_file = request.form['save_file'].encode('utf-8')
            link = request.form['link'].encode('utf-8')

            if file == '' or name == '' or (link != '0' and link != '1'):
                return_json = {'success': 0, 'error_msg': 'POST数据格式有误'}
                return Response(json.dumps(return_json), mimetype='application/json')

            # 检查文件是否存在
            _file = file.replace('/' + name, '')

            if _file == '':
                _file = '/'

            result = bdce.check_file(_file, name.decode('utf-8'))

            if result != False:
                # 获取下载地址
                url = bdce.get_download_url(file, link)

                # 设置默认路径
                if save_file == '':
                    save_file = sys.path[0]
                # 添加任务
                task_id = de.add_task(url, name, result['size'], save_file + '/' + name)
                if task_id != -1:
                    res = {'success': 1, 'task_id': task_id}
                    return Response(json.dumps(res), mimetype='application/json')

                # 错误
                pushCommand = utils.last_msg
                res = {'success': 0, 'error_msg': 'See the console.'}
                return Response(json.dumps(res), mimetype='application/json')

        elif action == 'start':
            task_id = request.form['task_id'].encode('utf-8')

            if de.start_task(int(task_id)):
                res = {'success': 1}
                return Response(json.dumps(res), mimetype='application/json')
            else:
                # 错误
                pushCommand = utils.last_msg
                res = {'success': 0, 'error_msg': 'See the console.'}
                return Response(json.dumps(res), mimetype='application/json')

        elif action == 'pause':
            task_id = request.form['task_id'].encode('utf-8')

            if de.pause_task(int(task_id)):
                res = {'success': 1}
                return Response(json.dumps(res), mimetype='application/json')
            else:
                # 错误
                pushCommand = utils.last_msg
                res = {'success': 0, 'error_msg': 'See the console.'}
                return Response(json.dumps(res), mimetype='application/json')

        elif action == 'delete':
            task_id = request.form['task_id'].encode('utf-8')

            if de.delete_task(int(task_id)):
                res = {'success': 1}
                return Response(json.dumps(res), mimetype='application/json')
            else:
                # 错误
                pushCommand = utils.last_msg
                res = {'success': 0, 'error_msg': 'See the console.'}
                return Response(json.dumps(res), mimetype='application/json')
        else:
            res = {'success': 0, 'error_msg': '未知action'}
            return Response(json.dumps(res), mimetype='application/json')




@app.route('/pushcommand/')
def pushcommand():
    global de
    global pushCommand
    global tmp_lastmsg

    if tmp_lastmsg != utils.last_msg:
        pushCommand = utils.last_msg
        tmp_lastmsg = utils.last_msg

    res = {'pushCommand': pushCommand, 'task_ranges': []}
    for task in de.task_list:
        res['task_ranges'].append(task.ranges)

    return Response('data:%s \n\n' % json.dumps(res), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)