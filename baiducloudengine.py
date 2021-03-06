# coding=utf-8
import utils
import errmsg

import re
import io
import os
import traceback
import base64
import json
import requests
import random

from Crypto.PublicKey import RSA
from Crypto.Cipher    import PKCS1_v1_5
# Crypto代替rsa参考：https://git.wageningenur.nl/aflit001/ibrowser/commit/1b2437fe81af9a8511bf847c1ada69a9de8df893?view=parallel&w=1

# 兼容2.7和3.x
try:
    import cookielib
    import urllib
except ImportError:
    import http.cookiejar as cookielib
    import urllib.parse as urllib

'''
这是一个百度云引擎模块
目前已经实现功能：
登陆
退出登陆
自动登录

目标功能：
获取文件目录
获取下载链接
获取文件大小
'''

home_url = 'https://pan.baidu.com'
passport_url = 'https://passport.baidu.com/v2/api/?'
logout_url = 'https://passport.baidu.com/?logout&u=https%3A%2F%2Fpan.baidu.com%2F'
# 验证码
captcha_url = 'https://passport.baidu.com/cgi-bin/genimage?'
pan_api_url = 'http://pan.baidu.com/api/'
disk_home_url = 'https://pan.baidu.com/disk/home'
pcs_rest_url = 'http://d.pcs.baidu.com/rest/2.0/pcs/file'
get_publickey_url = 'https://passport.baidu.com/v2/getpublickey?token='

max_retry_times = 10

class BaiduCloudEngine():
    def __init__(self, webserver=False, user_agent='netdisk;4.6.2.0;PC;PC-Windows;10.0.10240;WindowsBaiduYunGuanJia'):
        '''
        初始化百度云引擎
        
        私有变量self.window为当前的WindowEngine句柄
        私有变量self.cj为cookie
        私有变量self.opener为urllib2的opener
        私有变量self.headers为自定义user-agent
        
        :param window：当前WindowEngine句柄，默认为None
        :param user_agent: 默认为win10 chrome
        '''

        self.webserver = webserver
        self.session = requests.session()

        self.headers = { 'Accept':'*/*',
                    'Accept-Encoding':'gzip, deflate',
                    'Accept-Language':'zh-CN,zh;q=0.8',
                    'User-Agent': user_agent
        }

        self.file_list = {}

        # 用于网页模式
        self.verifycode = ''
        self.verifycode_img_url = ''
        self.mail_verify_mode = False

        # 读取cookie
        cookie = self.get_cookies()
        if cookie is not None and cookie is not False:
            self.session.cookies = cookie
            self.get_token()
            self.logined = True
        else:
            self.logined = False

    def get_session(self):
        return self.session
    
    def get_headers(self):
        return self.headers
    
    def get_response(self, url, post_data=None, html=True, headers=None):
        '''
        获取http返回内容
        
        :param url: 地址
        :param post_data: post数据，默认为None
        :param html: 是否请求的是html数据
        :param headers: 可以自定义请求头
        :returns: http返回内容，错误返回''
        '''
        
        req_headers = self.headers
        
        if headers is not None:
            for header in headers:
                req_headers[header] = headers[header]
        
        tryed_time = 0
        while tryed_time <= 3:
            try:
                if post_data is None:
                    response = self.session.get(url, headers=req_headers)
                else:
                    response = self.session.post(url, data=post_data, headers=req_headers)
                break
            except Exception:
                tryed_time += 1
                utils.show_msg('Get url %s timeout, tryedtime=%d' % (url, tryed_time))
        
        if tryed_time > 3:
            utils.show_msg(traceback.print_exc())

            if post_data is not None:
                utils.show_msg('错误：Post url %s failed.' % url)
            else:
                utils.show_msg('错误：Open url %s failed.' % url)

            return ''

        return response.content

    def check_login(self, username):
        '''
        检查登陆信息，获取token和codestring
        此函数不再使用
        
        :param username: 用户名
        :returns: 正常返回值为string格式值为codestring
                  0为失败，None为发生错误
        '''
        
        response =  self.get_response(home_url)

        if response == '':
            return False
        else:
            # 获取dv
            try:
                tmp = re.findall('id=\"dv_Input\" type=\"hidden\" value=\"(.*?)\"', response)

            except Exception:
                utils.show_msg(traceback.print_exc())
                utils.show_msg('错误：Can\'t get dv_Input.')
                return False
        
        codestring = None

        if not self.get_token():
            return False

        # logincheck
        passport_logincheck_url = passport_url + 'logincheck&&token=%s' % self.token
        passport_logincheck_url += '&tpl=pp&apiver=v3&tt=%s' % utils.get_time()
        passport_logincheck_url += '&username=%s' % urllib.quote(username)
        passport_logincheck_url += '&isphone=false&callback=bd__cbs__' + utils.get_callback_function()
        passport_logincheck_response = self.get_response(passport_logincheck_url)

        json = utils.get_json_from_response(passport_logincheck_response)

        try:
            json = eval(json[0])
            codeString = json['data']['codeString']
            
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误:Can\'t get passport logincheck\'s response json.')
            return False
        
        return codeString

    def get_token(self):
        '''
        通过getapi获取token

        :returns: False为发生错误
        '''

        passport_getapi_url = passport_url + 'getapi&tpl=pp&apiver=v3&tt=%s' % utils.get_time()
        passport_getapi_url += '&class=login&logintype=basicLogin&callback=bd__cbs__' + utils.get_callback_function()
        passport_getapi_response = self.get_response(passport_getapi_url)

        json = utils.get_json_from_response(passport_getapi_response)

        try:
            json = eval(json[0])
            self.token = json['data']['token']
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t get passport getapi\'s response json.')
            return False

        return True

    def get_publickey(self, ):
        '''
        参考自https://github.com/ly0/baidupcsapi/blob/master/baidupcsapi/api.py
        根据项目部分修改
        '''
        url = get_publickey_url + self.token
        content = self.get_response(url)
        jdata = json.loads(content.replace(b'\'', b'"').decode('utf-8'))

        return jdata['pubkey'], jdata['key']

    def get_verifycode(self):
        '''
        命令行模式获取用户输入的验证码，网页服务器模式获取验证码地址

        :returns: 若开启了网页服务器返回值为False,否则返回用户输入的验证码
        '''
        from PIL import Image

        if self.codestring != '':
            # 验证码
            verifycode_img_url = captcha_url + self.codestring
            if self.webserver:
                self.verifycode_img_url = verifycode_img_url
                self.verifycode = ''
                return False
            else:
                verifycode_img_response = self.get_response(verifycode_img_url, html=False)
                verifycode_img_bytes = io.BytesIO(verifycode_img_response)
                verifycode_img = Image.open(verifycode_img_bytes)
                verifycode_img.show()

                # 兼容3.x
                try:
                    captch = raw_input("Enter verifycode：")
                except NameError:
                    captch = input("Enter verifycode：")

                verifycode_img.close()
        else:
            captch = ''

        return captch

    def login(self, username, password, verify='', mail_verify=''):
        '''
        进行登陆
        
        可能会弹出窗口输入验证码
        
        :param username: 用户名
        :param password:密码
        :param verify: 验证码，默认为空
        :returns: -1为错误，1为成功，2为需要验证码，3为需要邮箱验证码
        '''

        # 如果是验证邮箱mode
        if self.mail_verify_mode:
            if self.check_mail_verify_code(mail_verify):
                self.login_success()
                return 1
            else:
                return -1

        retry = 0
        
        while retry <= max_retry_times:
            if self.verifycode != '':
                captch = self.verifycode
                self.verifycode_img_url = ''
                self.verifycode = ''
            else:
                '''
                self.codestring = self.check_login(username)

                if self.codestring == 0:
                    return False

                if self.codestring is None:
                    utils.show_msg('错误:codestring is None.')
                    return False
                '''
                if not self.get_token():
                    return -1
                self.codestring = ''

                captch = self.get_verifycode()
                # 如果为网页模式则返回2
                if captch is False:
                    return 2

            # 此处参考自https://github.com/ly0/baidupcsapi/blob/master/baidupcsapi/api.py
            pubkey, rsakey = self.get_publickey()
            key = RSA.importKey(pubkey)
            password_rsaed = base64.b64encode(PKCS1_v1_5.new(key).encrypt(password.encode('utf-8')))
            # 以上为参考，变量、函数名、使用函数根据项目需求略微修改

            #计算gid
            gid = "xxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
            for i in xrange(29):
                gid = re.sub('x', utils.get_gid_char(0), gid,1)
            gid = re.sub('y', utils.get_gid_char(8), gid,1)

            post_data = {"staticpage": "http://www.baidu.com/cache/user/html/v3Jump.html",
                         "charset": "utf-8",
                         "token": self.token,
                         "tpl": "pp",
                         "subpro": "",
                         "apiver": "v3",
                         "tt": utils.get_time(),
                         "codestring": self.codestring,
                         "safeflg": "0",
                         "u": "https://passport.baidu.com/",
                         "isPhone": "false",
                         "quick_user": "0",
                         "logintype": "basicLogin",
                         "logLoginType": "pc_loginBasic",
                         #"idc": "",
                         "loginmerge": "true",
                         "username": username,
                         "password": password_rsaed,
                         "verifycode": captch,  # 验证码
                         "mem_pass": "on",
                         "rsakey": str(rsakey),
                         "crypttype": "12",
                         "ppui_logintime": random.randint(10000,99999),
                         "callback": "parent.bd__pcbs__" + utils.get_callback_function(),
                         "detect": 1,
                         "foreignusername": "",
                         "gid": gid
                        }

            '''
            gid 原始代码：
            return "xxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(e) {
                var t = 16 * Math.random() | 0
                  , n = "x" == e ? t : 3 & t | 8;
                return n.toString(16)
            }).toUpperCase()

            分析后得出此代码为：x填充16进制随机数，y填充大于等于8的16进制随机数
            '''

            passport_logincheck_response = self.get_response(passport_url + 'login', post_data)
            
            try:
                tmp = re.findall('decodeURIComponent\(\"(.*?)\"\)', passport_logincheck_response)
                jump_url = tmp[0]
                jump_url = jump_url.replace('\\', '')
                tmp = re.findall('accounts\s*?=\s*?\'(.*?)\'', passport_logincheck_response)
                account = tmp[0]
                jump_url += '?'
                tmp = re.findall('href\s*?\+=\s*?"(.*?)"', passport_logincheck_response)
                jump_url += tmp[0]
                jump_url += account
                
            except Exception:
                utils.show_msg(traceback.print_exc())
                utils.show_msg('错误:Can\'t go to jump page.')
                return -1
            
            # 错误处理
            try:
                tmp = re.findall('err_no=([-]?\d*)', jump_url)
                errno = tmp[0]
            except Exception:
                utils.show_msg(traceback.print_exc())
                utils.show_msg('错误:Can\'t get check login error number.')
                return -1
            
            if errno == '3' or errno == '6' or errno == '200010':
                # 验证码错误，需要重新输入
                pass

            elif errno == '257':
                # 未输入验证码或者首次登陆需要获取验证码
                tmp = re.findall('&codeString=([A-Za-z0-9]*?)&userName', passport_logincheck_response)
                if len(tmp) > 0:
                    self.codestring = tmp[0]
                else:
                    utils.show_msg('错误：无法获取codeString信息.')
                    return -1

                # 获取当前验证码
                result = self.get_verifycode()

                if result is False:
                    # 如果为网页模式则返回False
                    utils.show_msg('错误:登陆错误，请重新尝试，错误代码：' + errno + '，错误信息：' + errmsg.get_login_errmsg(errno))
                    return 2
                else:
                    # 如果为命令行模式则直接进入下一次循环
                    self.verifycode = result
                    continue

            elif errno == '0' or errno == '18' or errno == '400032' or errno == '400034' or errno == '400037' or errno == '400401':
                self.login_success()

                return 1
            
            elif errno == '120019':
                utils.show_msg('错误：%s，短时间密码错误次数过多, 请先通过 passport.baidu.com 解除锁定' % errno)
                return -1
            elif errno == '120021':
                # 用户需要外部认证(邮箱)
                self.auth_token = re.findall('authtoken=([^&]+)', passport_logincheck_response)[0]
                self.loginproxy_url = re.findall('loginproxy=([^&]+)', passport_logincheck_response)[0]
                responese = self.get_response('https://passport.baidu.com/v2/sapi/authwidgetverify' +
                                              '?authtoken=' + self.auth_token +
                                              '&type=email' +
                                              '&apiver=v3' +
                                              '&action=send' +
                                              '&vcode=' +
                                              '&questionAndAnswer=' +
                                              '&needsid=' +
                                              '&rsakey=' +
                                              '&countrycode=' +
                                              '&subpro=' +
                                              '&callback=' +
                                              '&tpl=mn' +
                                              '&u=https://www.baidu.com/'
                                            )
                responese = json.loads(responese)
                if responese['errmsg'] is None:
                    if self.webserver:
                        # 如果是网页模式，直接返回3
                        self.mail_verify_mode = True
                        return 3
                    else:
                        self.check_mail_verify_code(input('请输入邮箱验证码：'))

                else:
                    utils.show_msg('错误：发送安全验证请求失败')
                    return -1

            utils.show_msg('错误:登陆错误，请重新尝试，错误代码：' + errno + '，错误信息：' + errmsg.get_login_errmsg(errno))
            retry += 1

        utils.show_msg('错误:超出最大重试次数：' + str(max_retry_times))
        return -1

    def check_mail_verify_code(self, vcode):
        '''
        验证邮箱验证码

        :param vcode: 邮箱验证码
        :return: True为成功，False为失败或发生错误
        '''
        responese = self.get_response('https://passport.baidu.com/v2/sapi/authwidgetverify' +
                                      '?authtoken=' + self.auth_token +
                                      '&type=email' +
                                      '&apiver=v3' +
                                      '&action=check' +
                                      '&vcode=' + str(vcode) +
                                      '&questionAndAnswer=' +
                                      '&needsid=' +
                                      '&rsakey=' +
                                      '&countrycode=' +
                                      '&subpro=' +
                                      '&callback=')
        responese = json.loads(responese)
        if responese['errno'] == 110000:
            loginproxy_resp = self.get_response(urllib.unquote(self.loginproxy_url.decode()))
            self.mail_verify_mode = False
            return True
        else:
            utils.show_msg('错误:邮箱验证码错误' + responese['errno'])
            return False

    def login_success(self):
        '''
        登陆成功后执行，并设置logined状态

        '''
        self.get_response(disk_home_url)

        self.save_cookies()

        self.logined = True

    def logout(self):
        '''
        退出登陆
        
        :returns: True为成功，False为失败或发生错误
        '''
        
        #passport_logout_response = self.get_response(logout_url)

        self.session.cookies = cookielib.CookieJar()
        response = self.get_response(logout_url)
        check_logout = re.findall('login-main', response)

        if len(check_logout) > 0:
            self.logined = False
            self.remove_cookies()
            return True
        else:
            return False

    def save_cookies(self):
        '''
        保存cookie

        :returns: True为成功，False为失败或发生错误
        '''

        try:
            if os.path.isfile('cookie.list'):
                os.remove('cookie.list')

            fd = open('cookie.list', "wb+")

            cookie_list = requests.utils.dict_from_cookiejar(self.session.cookies)

            fd.write(json.dumps(cookie_list))
            fd.close()

            return True
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t save cookie list file.')
            return False

    def get_cookies(self):
        '''
        读取cookie

        :returns: 返回值直接赋值给requests.session()，None为无cookie
        '''

        response = self.get_response(home_url)
        if response is False:
            return False

        try:
            if os.path.isfile('cookie.list'):
                fd = open('cookie.list', "rb+")
            else:
                return None

            cookie = fd.read()
            fd.close()

            if cookie == '':
                return None
            else:
                return requests.utils.cookiejar_from_dict(json.loads(cookie))

        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Can\'t get cookie list file.')
            return False

    def remove_cookies(self):
        '''
        删除cookie
        '''
        if os.path.exists('cookie.list'):
            os.remove('cookie.list')

    def do_pan_api(self, api, args):
        '''
        执行百度网盘api
        
        :param api: 需要执行的api
        :param args: string格式参数
        :returns: 结果True or False
        '''
        api_url = pan_api_url + api + '?'
        api_url += 'channel=chunlei&clienttype=0&web=1&t=%s' % utils.get_time()
        api_url += '&bdstoken=' + self.token
        
        for arg in args:
            api_url += '&%s=%s' % (arg, args[arg])
            
        pan_api_response = self.get_response(api_url)
        
        json = pan_api_response

        try:
            json = eval(json)
            errno = str(json['errno'])

            if errno == '0':
                return json['list']
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg("错误:Can't get pan api:" + api + " response json.")
            return False
        
        # 错误处理
        if errno == '-6':
            # cookie失效
            self.logined = False
            self.remove_cookies()
            utils.show_msg('错误:cookies已失效，请刷新页面重新登陆')
        else:
            utils.show_msg('错误:执行百度云api：' + api + '时出错，错误代码：' + errno + '，错误信息：' + errmsg.get_errmsg_by_errno(errno))

        return False
    
    def get_list(self, dir, page=None, page_size=None, order='name', desc='1'):
        '''
        获取目录列表，默认全部获取
        
        注意输入必须全是string格式
        
        :param dir：目录路径
        :param page：第几页
        :param page_size：每页几条记录，默认20
        :param order: 排序字段
                      可选：time  修改时间
                           name  文件名
                           size  大小，注意目录无大小
        :param desc：1为降序，0为升序，默认为降序
        :returns: dict格式文件信息，server_filename和path为unicode编码，错误返回False
        '''
        
        args = {
            "_": utils.get_time(),
            "dir": urllib.quote(dir),
            "order": order,
            "desc" : desc,
        }
        
        if page is not None:
            args['page'] = page
        if page_size is not None:
            args['num'] = page_size

        result = self.do_pan_api('list', args)

        if result != False:
            for file in result:
                file['server_filename'] = eval('u\'' + file['server_filename'] + '\'')
                file['path'] = eval('u\'' + file['path'] + '\'.replace(\'\\\\\',\'\')')

            self.file_list[dir] = result

        return result
        
    def get_download_url(self, dir, link):
        '''
        获取下载链接
        
        :param dir: 目录
        :returns: string格式下载链接
        '''

        if link == '0':
            url = self.get_baiducloudclient_url(dir)
        else:
            url = pcs_rest_url
            url += '?method=%s&app_id=%s&path=%s' % ('download', '250528', urllib.quote(dir))

        return url
    
    def get_file_size(self, url):
        '''
        获取文件大小

        :param url: 文件链接
        :return: 文件大小，错误返回False
        '''
        headers = {
            'Range': 'bytes=0-4'
        }

        try:
            response = self.session.get(url, headers=headers)
        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Get file size failed.url %s.' % url)
            return False

        content_range = response.headers['content-range']
        size = int(re.match('bytes 0-4/(\d+)', content_range).group(1))
        
        return size

    def check_file(self, dir, file_name):
        '''
        检查在已缓存文件list中是否存在文件

        :param dir: 路径，不包含文件名，结尾无/
        :param file_name: 文件名
        :return: json格式文件信息，server_filename和path为unicode编码，错误返回False
        '''
        try:
            for file in self.file_list[dir]:
                if file['server_filename'] == file_name:
                    return file
        except Exception:
            utils.show_msg('错误：Check file failed.')
            return False

    def get_baiducloudclient_url(self, dir):
        headers = {
            'User-Agent': 'netdisk;4.6.2.0;PC;PC-Windows;10.0.10240;WindowsBaiduYunGuanJia'
        }

        # 申请加速，若失败自动获取的是普通链接
        url = 'https://pan.baidu.com/rest/2.0/membership/speeds/freqctrl'
        postdata = {
            'method': 'consume'
        }
        '''
        get为获取是否可以使用状态，freq_cnt=1时可以使用
        consume为获取链接
        '''

        try:
            responese = self.get_response(url, post_data=postdata, headers=headers)

        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Get file size failed.url %s.' % url)
            return False

        # 获取链接
        url = 'https://d.pcs.baidu.com/rest/2.0/pcs/file?time=' + utils.get_time() + '&clienttype=21&version=2.1.0&vip=0&method=locatedownload&app_id=250528&esl=1&ver=4.0&dtype=1&ehps=1&check_blue=1&path=' + dir + '&err_ver=1.0'

        try:
            response = self.get_response(url, headers=headers)

        except Exception:
            utils.show_msg(traceback.print_exc())
            utils.show_msg('错误：Get file size failed.url %s.' % url)
            return False

        # 获取第一个url
        url_info = json.loads(response)

        return url_info['urls'][0]['url']