# coding=utf-8
from baiducloudengine import BaiduCloudEngine
from windowengine import WindowEngine

import downloadengine
import utils
import sys

username = ''
password = ''

user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
#user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

def test(bdce):
    url = bdce.get_download_url('/leanote-desktop-mac-v2.2.3.zip')
    size = bdce.get_file_size(url)
    
    if not size:
        return 0
    task_id = downloadengine.add_task(bdce, url, size, '/Users/eddieyang/Documents/workspace/baiducloudhelper/test.zip')
    
    if task_id != -1 | task_id != False:
        downloadengine.start_task(task_id)
    
def run(username, password):
    bdce = BaiduCloudEngine()
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
        # 初始化WindowEngine会自动初始化一个BaiduCloudEngine，全部工作交给WindowEngine处理
        we = WindowEngine()
    else:
        run(username, password)
    
    
if __name__ == "__main__":
    main(sys.argv[1:])