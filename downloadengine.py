# coding=utf-8
import utils

from threadpool import *
import traceback
import os
import json

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

DownloadTask 为任务类，仅供下载引擎类使用
DownloadEngine 为下载引擎

线程数由DownloadEngine.thread_num控制，为全局参数
分块区间为初始化DownloadTask时设定，任务一旦创建则无法修改下载区块设置
修改线程数必须在暂停所有任务之后才可以！！
'''

class DownloadTask:
    def __init__(self, bdce, url, name, size, save_file, ranges, from_file=False):
        '''
        新建初始化
        
        :param bdce：百度云引擎，用于获取：登陆cookie、headers
        :param url：下载链接
        :param name: 文件名
        :param size：文件大小
        :param save_file：保存文件名
        :param from_file: 是否是从已存在任务配置文件初始化，默认为False
        '''
        
        self.cookies = bdce.get_cookies()
        self.headers = bdce.get_headers()
        self.url = url
        self.name = name
        self.size = size
        self.save_file = save_file
        self.ranges = ranges
        # 任务下载状态 0为未下载完成 1为下载中 2为下载完成
        self.download_status = 0
        # 为了便于计算文件是否下载完成，设置个计数器
        self.downloaded_range_num = 0

        if from_file:
            self.get_task_info()
        
    def save_task_info(self):
        '''
        保存任务配置文件

        :return: 结果True or False
        '''
        info = {
            'headers': self.headers,
            'url': self.url,
            'name': self.name,
            'size': self.size,
            'save_file': self.save_file,
            'ranges': self.ranges,
            'download_status': self.download_status,
            'downloaded_range_num': self.downloaded_range_num
            }
        
        info = str(info)
        try:
            fd = open(self.save_file + '.info', "w")
            fd.write(info)
            fd.close()
            
            return True
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t save .info file.')
            return False
        
    def get_task_info(self):
        '''
        获取任务配置文件

        :return: 结果True or False
        '''
        try:
            fd = open(self.save_file + '.info', "r")
            info = eval(fd.read())
            fd.close()
            
            self.headers = info['headers']
            self.url = info['url']
            self.name = info['name']
            self.size = info['size']
            self.save_file = info['save_file']
            self.ranges = info['ranges']
            self.download_status = info['download_status']
            self.downloaded_range_num = info['downloaded_range_num']
            
            return True
        except IOError:
            return False
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t get .info file.')
            return False
    
    def create_tmp_file(self):
        '''
        创建临时文件

        :return: 结果True or False
        '''
        try:
            fd = open(self.save_file + '.tmp','wb')
            fd.close()
            
            return True
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t create temp file.')
            return False

class DownloadEngine:
    def __init__(self, bdce, thread_num=10, webserver=False):
        '''
        初始化

        :param bdce: 百度云引擎
        :param webserver: 是否为网页服务启动，默认为False
        '''

        self.bdce = bdce
        # 是否为web服务调用
        self.webserver = webserver
        # 每个区块大小，目前默认为10M
        self.delta_range = 1024 * 1024 * 10
        # 线程数
        self.thread_num = thread_num
        # 创建线程池
        self.pool = None

        # 读取已存任务列表
        task_list = self.get_task_file()
        if task_list != False:
            self.task_list = task_list
        else:
            self.task_list = []

    def get_task_file(self):
        '''
        读取任务列表文件

        :return: list格式任务列表，错误返回False
        '''

        try:
            if not os.path.isfile('task.list'):
                fd = open('task.list', "wb+")
            else:
                fd = open('task.list', "rb+")

            tasks = fd.read()
            fd.close()

            # 初始化task任务
            if tasks == '':
                return []
            else:
                _task = []
                task_list = json.loads(tasks)

                for task in task_list:
                    if os.path.isfile(task['save_file'] + '.info'):
                        tmp_task = DownloadTask(self.bdce, '', '', 0, task['save_file'], [], True)
                        # 检查是否初始化正常
                        if tmp_task.url == '' and tmp_task.name == '' and tmp_task.size == 0 and tmp_task.ranges == []:
                            utils.show_msg('错误：加载配置文件：%s 失败，请自行删除无用配置文件和缓存文件' % task['save_file'] + '.info')
                        else:
                            _task.append(tmp_task)

                return _task

        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t get task list file.')
            return False

    def save_task_file(self):
        '''
        保存任务列表

        :return:结果True or False
        '''

        try:
            fd = open('task.list', "wb+")
            # 将任务对象转为dict
            _task_list = []
            for task in self.task_list:
                _task_list.append({
                    'url': task.url,
                    'name': task.name,
                    'size': task.size,
                    'save_file': task.save_file
                })

            fd.write(json.dumps(_task_list))
            fd.close()

            return True
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t save task list file.')
            return False

    def get_ranges(self, size):
        '''
        获取下载的区块区间

        :param size: 文件大小
        :return: list格式区块区间[start, end, downloaded]
        '''

        ranges = []
        _size = 0

        while _size < size and size > _size + self.delta_range:
            ranges.append((_size, _size + self.delta_range, 0))
            _size += self.delta_range + 1

        ranges.append((_size, size, 0))

        return ranges

    def download(self, task, range_id):
        '''
        下载线程调用的函数

        :param task: 任务对象
        :param range_id: 需要下载的区块所在id
        :return: 结果True or False
        '''

        range = task.ranges[range_id][0:2]

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
                utils.show_msg(traceback.print_exc())
                utils.show_msg('错误：Get range (%d,%d) failed.' % range)

        res = response.read()

        encoding = response.info().get('Content-Encoding')
        if encoding == 'gzip':
            res = utils.gzip_decode(res)
        elif encoding == 'deflate':
            res = utils.deflate_decode(res)

        # 写入文件
        try:
            f = open(task.save_file + '.tmp', 'rb+')
            f.seek(range[0], 0)
            f.write(res)
            f.close()

        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t write to tmp file')
            print(range)
            return False

        task.ranges[range_id] = (range[0], range[1], 1)
        task.downloaded_range_num += 1

        print("(%d,%d) download success" % range)

        # 检测是否下载完成
        if task.downloaded_range_num == len(task.ranges):
            task.download_status = 2
            # 下载完成，删除配置文件，并修改文件名
            try:
                os.remove(task.save_file + '.info')
                os.rename(task.save_file + '.tmp', task.save_file)

                return True
            except:
                utils.show_msg(traceback.print_exc())
                utils.show_msg('错误：删除配置文件，并修改文件名失败，文件已下载完成，可自行修改文件名')
                return False

        else:
            # 保存下载配置文件
            if task.save_task_info():
                return True
            else:
                return False

    def add_task(self, url, name, size, save_file):
        '''
        添加任务

        :param url: 下载链接
        :param name: 文件名
        :param size: 文件大小
        :param save_file: 保存目录
        :return: 任务id，错误返回-1
        '''

        # 查找是否已存在任务
        for task in self.task_list:
            if task.url == url  and task.save_file == save_file:
                utils.show_msg('错误：任务已存在')
                return -1

        # 查看是否已存在文件
        if os.path.isfile(save_file):
            utils.show_msg('错误：文件已存在')
            return -1


        # 创建一个下载任务，并保存任务列表
        task = DownloadTask(self.bdce, url, name, size, save_file, self.get_ranges(size))


        # 检测任务文件
        if not task.get_task_info():
            # 写入配置文件和创建临时文件
            if not (task.save_task_info() & task.create_tmp_file()):
                utils.show_msg('错误：创建文件失败')
                return -1

        self.task_list.append(task)
        self.save_task_file()

        return len(self.task_list) - 1

    def start_task(self, id):
        '''
        开始任务

        :param id: 任务id
        :return: 结果True or False
        '''
        try:
            task = self.task_list[id]
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：任务不存在')
            return False

        if task.download_status == 1:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：任务正在下载中')
            return False
        elif task.download_status == 2:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：任务已完成，请删除后移除下载完成的文件重新下载')
            return False

        args = []
        for range in task.ranges:
            if range[2] == 0:
                download_args = [task, task.ranges.index(range)]
                args.append((download_args, None))


        requests = makeRequests(self.download, args)

        self.pool = ThreadPool(self.thread_num)

        for req in requests:
            self.pool.putRequest(req)

        task.download_status = 1
        utils.show_msg('Start downloading')
        #pool.wait()

        return True

    def pause_task(self, task_id):
        '''
        暂停任务

        :param task_id: 任务id
        '''
        try:
            self.task_list[task_id].download_status = 0
            self.pool.dismissWorkers(len(self.pool.workers))

            return True
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：DismissWorkers error.')
            return False

    def delete_task(self, task_id):
        '''
        删除任务

        :param task_id: 任务id
        '''


        try:
            del(self.task_list[task_id])
            self.save_task_file()

            return True
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Delete task:%d error.' % task_id)
            return False