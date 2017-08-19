# coding=utf-8
from baiducloudengine import BaiduCloudEngine
from downloadengine import DownloadEngine

import os
import utils
import sys

# 注意命令行运行用于开发调试，请勿继续使用
username = ''
password = ''
disk_file = ''
file_name = ''
download_file = ''

user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
#user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

def download(bdce):
    url = bdce.get_download_url(disk_file, 1) # 0为普通直链，1为特殊链
    size = bdce.get_file_size(url)
    
    if not size:
        return 0

    de = DownloadEngine(bdce)
    task_id = de.add_task(url, file_name, size, download_file)

    if task_id != -1 | task_id != False:
        de.start_task(task_id)

def download_task(bdce, task_id):
    de = DownloadEngine(bdce)
    de.start_task(task_id)
    input("\n\nPress the enter key to exit.")

def run():
    bdce = BaiduCloudEngine()

    if username == '' or password == '':
        utils.show_msg('请打开main.py修改相关信息')
        return False

    if bdce.logined:
        utils.show_msg('登录成功')
        download_task(bdce, 1)
    else:
        if bdce.login(username, password):
            utils.show_msg('登录成功')
            download_task(bdce, 1)
        else:
            utils.show_msg('登录失败')
            return 0
    
    #if bdce.logout():
    #   utils.show_msg('退出登录成功')
    #else:
    #    utils.show_msg('退出登录失败')
    #    return 0
    
def main(argv):
    if '-w' in argv:
        os.system('python ' + sys.path[0] + '/webserver.py')
    else:
        run()

    
if __name__ == "__main__":
    main(sys.argv[1:])