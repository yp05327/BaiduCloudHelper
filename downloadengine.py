# coding=utf-8
import baiducloudengine
import utils

import multiprocessing
from threadpool import *
import traceback
import random
import os

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
    def __init__(self, bdce, url, size, save_file, thread_num=10):
        '''
        初始化
        
        Args:
            bdce：百度云引擎，用于获取：登陆cookie、headers
            url：下载链接
            size：文件大小
            save_file：保存文件名
            thread_num：线程数，默认10
        '''
        
        self.cookies = bdce.get_cookies()
        self.headers = bdce.get_headers()
        self.url = url
        self.size = size
        self.save_file = save_file
        self.ranges = self.get_ranges()
        
        self.thread_num = thread_num
        '''
        # 修正输入的线程数
        if len(self.ranges) < thread_num:
            self.thread_num = len(self.ranges)
        else:
            self.thread_num = thread_num
        '''
        
    def save_task_info(self):
        cookies = []
        for cookie in self.cookies:
            cookies.append({
                    'version': cookie.version,
                    'name': cookie.name,
                    'value': cookie.value,
                    'port': cookie.port,
                    'port_specified': cookie.port_specified,
                    'domain': cookie.domain,
                    'domain_specified': cookie.domain_specified,
                    'path': cookie.path,
                    'path_specified': cookie.path_specified,
                    'secure': cookie.secure,
                    'expires': cookie.expires,
                    'discard': cookie.discard,
                    'comment': cookie.comment,
                    'comment_url': cookie.comment_url,
                    'rest': cookie._rest,
                    'rfc2109': cookie.rfc2109
                })
            
        info = {
            'cookies': cookies,
            'headers': self.headers,
            'url': self.url,
            'size': self.size,
            'save_file': self.save_file,
            'thread_num': self.thread_num,
            'ranges': self.ranges
            }
        
        info = str(info)
        try:
            fd = open(self.save_file + '.info', "w")
            fd.write(info)
            fd.close()
            
            return True
        except Exception:
            utils.show_msg('错误：Can\'t save .info file.', window)
            utils.show_msg(traceback.print_exc())
            return False
        
    def get_task_info(self):
        try:
            fd = open(self.save_file + '.info', "r")
            info = eval(fd.read())
            fd.close()
            
            cookies = cookielib.CookieJar()
            for cookie in info['cookies']:
                cookies.set_cookie(cookielib.Cookie(
                        version=cookie['version'],
                        name=cookie['name'],
                        value=cookie['value'],
                        port=cookie['port'],
                        port_specified=cookie['port_specified'],
                        domain=cookie['domain'],
                        domain_specified=cookie['domain_specified'],
                        domain_initial_dot=False,
                        path=cookie['path'],
                        path_specified=cookie['path_specified'],
                        secure=cookie['secure'],
                        expires=cookie['expires'],
                        discard=cookie['discard'],
                        comment=cookie['comment'],
                        comment_url=cookie['comment_url'],
                        rest=cookie['rest'],
                        rfc2109=cookie['rfc2109']
                    ))
            self.cookies = cookies
            self.headers,
            self.url = info['url']
            self.size = info['size']
            self.save_file = info['save_file']
            self.thread_num = info['thread_num']
            self.ranges = info['ranges']
            
            return True
        except IOError:
            return False
        except Exception:
            utils.show_msg('错误：Can\'t get .info file.')
            utils.show_msg(traceback.print_exc())
            return False
    
    def create_tmp_file(self):
        try:
            fd = open(self.save_file + '.tmp','wb')
            tmp = chr(1)
            for i in xrange(self.size - 1):
                tmp += chr(1)
                
            fd.write(tmp)
            fd.close()
            
            return True
        except Exception:
            utils.show_msg('错误：Can\'t create temp file.', window)
            utils.show_msg(traceback.print_exc())
            return False
        
    def get_ranges(self):
        '''
        获取每个线程下载的区块区间
        
        Returns:
            list格式区块区间
        '''
        
        ranges = []
        _size = 0
        
        while _size < self.size and self.size > _size + delta_range:
            ranges.append((_size, _size + delta_range))
            _size += delta_range + 1
        
        ranges.append((_size, self.size))
        
        return ranges

# 任务列表
task_list = []
window = None
# 每个区块大小
delta_range = 1024 * 1024 * 10

def download(task, range):
    # 设置 cookie
    cj = cookielib.CookieJar() 
    
    for cookie in task.cookies:
        cj.set_cookie(cookie)
        
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    
    headers = task.headers
    headers['Range'] = 'bytes=%d-%d' % range
    
    req = urllib2.Request(task.url, headers=headers)
    
    success = False
    
    while not success:
        try:
            response = opener.open(req)
            
            success = True
        except Exception:
            utils.show_msg('错误：Get range (%d,%d) failed.' % range)
            utils.show_msg(traceback.print_exc())
        
    res = response.read()

    encoding = response.info().get('Content-Encoding')
    if encoding == 'gzip':
        res = utils.gzip_decode(res)
    elif encoding == 'deflate':
        res = utils.deflate_decode(res)
        
    print("(%d,%d) download success" % range)
    
    # 写入文件
    try:
        f = open(task.save_file + '.tmp', 'rb+')
        f.seek(range[0], 0)
        f.write(res)
        f.close()
        
    except Exception:
        utils.show_msg('错误：Can\'t write to tmp file')
        utils.show_msg(traceback.print_exc())
        return False
    
    task.ranges.remove(range)
    if task.save_task_info():
        return True
    else:
        return False
           
def add_task(bdce, url, size, save_file, thread_num=10):
    # 查找是否已存在任务
    for task in task_list:
        if task.url == url  and task.save_file == save_file:
            utils.show_msg('错误：任务已存在')
            return False
    
    # 创建一个下载任务
    task = DownloadTask(bdce, url, size, save_file, thread_num=10)
    # 检测任务文件
    if not task.get_task_info():
        # 写入配置文件和创建临时文件
        if not (task.save_task_info() & task.create_tmp_file()):
            utils.show_msg('错误：创建文件失败')
            return False
    
    task_list.append(task)
    return len(task_list) - 1
    
def start_task(id):
    
    try:
        task = task_list[id]
    except Exception:
        utils.show_msg('错误：任务不存在', window)
        utils.show_msg(traceback.print_exc())
        return -1
    
    cookies = list(task.cookies)
    
    download_args = []
    args = []
    for range in task.ranges:
        download_args = [task, range]
        args.append((download_args, None))
    
    pool = ThreadPool(task.thread_num)  
    requests = makeRequests(download, args)  
    for req in requests:
        pool.putRequest(req)
    pool.wait()
    
    # 下载完成，删除配置文件，并修改文件名
    try:
        os.remove(task.save_file + '.info')
        os.rename(task.save_file + '.tmp', task.save_file)
        
        return True
    except:
        utils.show_msg('错误：删除配置文件，并修改文件名失败，文件已下载完成', window)
        utils.show_msg(traceback.print_exc())
        return False
