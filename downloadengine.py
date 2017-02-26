# coding=utf-8
import baiducloudengine
import utils

import multiprocessing
import traceback

# 兼容2.7和3.x
try:
    import urllib2
    import cookielib
    import urllib
except ImportError:
    import urllib.parse as urllib
    import urllib.request as urllib2
    import http.cookiejar as cookielib
    
'''
多线程下载引擎

'''

class DownloadTask:
    def __init__(self, bdce, url, size, save_name, thread_num=10):
        '''
        初始化
        
        Args:
            bdce：百度云引擎，用于获取：登陆cookie、headers
            url：下载链接
            size：文件大小
            save_name：保存文件名
            thread_num：线程数，默认10
        '''
        
        self.cookies = bdce.get_cookies()
        self.headers = bdce.get_headers()
        self.url = url
        self.size = size
        self.save_name = save_name
        self.thread_num = thread_num

    def get_range(self):
        '''
        获取每个线程下载的区块区间
        
        Returns:
            list格式区块区间
        '''
        
        ranges = []
        offset = int(int(self.size)/int(self.thread_num))
        for i in range(self.thread_num):
            if i == self.thread_num - 1:
                ranges.append((i*offset, ''))
            else:
                ranges.append((i*offset, (i+1)*offset-1))
                
        return ranges

# 任务列表
task_list = []
window = None

def download(cookies, url, headers, fd, start, end):
    # 设置 cookie
    cj = cookielib.CookieJar() 
    
    for cookie in cookies:
        cj.set_cookie(cookie)
        
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    
    headers = headers
    headers['Range'] = 'bytes=%s-%s' % (start, end)
    
    req = urllib2.Request(url, headers=headers)
    try:
        response = opener.open(req)
    except Exception:
        utils.show_msg('错误：Open url %s failed.' % url, window)
        utils.show_msg(traceback.print_exc())
        return ''
        
    res = response.read()
    
    encoding = response.info().get('Content-Encoding')
    if encoding == 'gzip':
        res = utils.gzip_decode(res)
    elif encoding == 'deflate':
        res = utils.deflate_decode(res)
    
    print("%s-%s download success" % (start,end))
    # 将文件指针移动到传入区间开始的位置
    fd.write(res)
           
def add_task(bdce, url, size, save_name, thread_num=10):
    # 查找是否已存在任务
    for task in task_list:
        if task.url == url  and task.save_name == save_name:
            utils.show_msg('错误：任务已存在')
            return False
    
    # 创建一个下载任务
    task = DownloadTask(bdce, url, size, save_name, thread_num=10)
    task_list.append(task)
    return len(task_list) - 1
 
def start_task(id):
    
    try:
        task = task_list[id]
    except Exception:
        utils.show_msg('错误：任务不存在', window)
        utils.show_msg(traceback.print_exc())
        return -1

    fd = open(task.save_name,"wb")
    
    # Windows平台要加上这句，避免 RuntimeError
    multiprocessing.freeze_support()
    pool = multiprocessing.Pool(processes=task.thread_num)
    
    cookies = list(task.cookies)

    for ran in task.get_range():
        # 获取每个线程下载的数据块
        start, end = ran
        handler = pool.apply_async(download, args=(cookies, task.url, task.headers, fd, start, end, ))
        handler.get()
    pool.close()
    pool.join()

    fd.close()