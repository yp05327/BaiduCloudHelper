# coding=utf-8
from baiducloudengine import BaiduCloudEngine
from windowengine import WindowEngine

import downloadengine
import utils

user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
#user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

def test(bdce):
    url = bdce.get_download_url('/新编第三册.rar')
    size = bdce.get_file_size(url)
    
    if not size:
        return 0
    task_id = downloadengine.add_task(bdce, url, size, 'test.zip')
    
    if task_id != -1:
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

def main():
    # 初始化WindowEngine会自动初始化一个BaiduCloudEngine，全部工作交给WindowEngine处理
    we = WindowEngine()
    
    
if __name__ == "__main__":
    main()