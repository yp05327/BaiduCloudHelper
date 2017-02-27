# coding=utf-8
from baiducloudengine import BaiduCloudEngine

import os
import downloadengine
import utils
import sys

username = ''
password = ''
disk_file = ''
download_file = ''

user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
#user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

def test(bdce):
    url = bdce.get_download_url(disk_file)
    size = bdce.get_file_size(url)
    
    if not size:
        return 0
    task_id = downloadengine.add_task(bdce, url, size, download_file)
    
    if task_id != -1 | task_id != False:
        downloadengine.start_task(task_id)
    
def run(username, password):
    bdce = BaiduCloudEngine()
    if username == '' or password == '':
        utils.show_msg('请打开main.py修改相关信息')
    return False

    if bdce.login(username, password):
        utils.show_msg('登录成功')
        test(bdce)
    else:
        utils.show_msg('登录失败')
        return 0
    
    if bdce.logout():
       utils.show_msg('退出登录成功')
    else:
        utils.show_msg('退出登录失败')
        return 0
    
def main(argv):
    if '-w' in argv:
        os.system('python ' + sys.path[0] + '/webserver.py')
    else:
        run(username, password)
    
    
if __name__ == "__main__":
    main(sys.argv[1:])