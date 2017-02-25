# coding=utf-8
import re
import io

# 兼容2.7和3.x
try:
    import urllib2
    import cookielib
    import urllib
except ImportError:
    import urllib.parse as urllib
    import urllib.request as urllib2
    import http.cookiejar as cookielib
    
from PIL import Image

import utils
import errmsg

'''
这是一个百度云引擎模块
目前已经实现功能：
登陆
退出登陆

目标功能：
获取文件目录
获取下载链接
'''

home_url = 'https://www.baidu.com'
passport_url = 'https://passport.baidu.com/v2/api/?'
logout_url = 'https://passport.baidu.com/?logout&u=http://pan.baidu.com'
captcha_url = 'https://passport.baidu.com/cgi-bin/genimage?'
pan_api_url = 'http://pan.baidu.com/api/'
disk_home_url = 'https://pan.baidu.com/disk/home'

max_retry_times = 3

class BaiduCloudEngine():
    def __init__(self, user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'):
        '''
        初始化百度云引擎
        
        私有变量self.__cj为cookie
        私有变量self.__opener为urllib2的opener
        私有变量self.__headers为自定义user-agent
        
        Args:
            user_agent:默认为win10 chrome
        '''
        
        self.__cj = cookielib.CookieJar() 
        self.__opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.__cj))
        self.__headers = { 'Accept':'*/*',
                    'Accept-Encoding':'gzip, deflate',
                    'Accept-Language':'zh-CN,zh;q=0.8',
                    'User-Agent': user_agent
        }
        
    def get_response(self, url, post_data=None, html=True):
        '''
        获取http返回内容
        
        Args:
            url:地址
            post_data:post数据，默认为None
            not_html":是否请求的是html数据
        Returns:
            http返回内容
        '''

        if post_data is not None:
            post_data = urllib.urlencode(post_data).encode(encoding='utf-8')
        
        req = urllib2.Request(url, data=post_data, headers=self.__headers)
        response = self.__opener.open(req)
        content = response.read()
        
        encoding = response.info().get('Content-Encoding')
        if encoding == 'gzip':
            content = utils.gzip_decode(content)
        elif encoding == 'deflate':
            content = utils.deflate_decode(content)
        
        # 3.x中为bytes类型，需要转成string
        if type(content) != type('') and html:
            content = content.decode()

        return content
    
    def check_login(self, username):
        '''
        检查登陆信息，获取token和codestring
        
        Args:
            username:用户名
        Returns:
            result:正常返回值为string格式值为codestring
                    0为失败，None为发生错误
        '''
        
        self.get_response(home_url)
        
        codestring = None
        
        # 通过getapi获取token
        passport_getapi_url = passport_url + 'getapi&tpl=netdisk&apiver=v3&tt='
        passport_getapi_url += utils.get_time() 
        passport_getapi_url += '&class=login&logintype=basicLogin&callback=bd__cbs__pwxtn7'
        passport_getapi_response = self.get_response(passport_getapi_url)
        
        json = utils.get_json_from_response(passport_getapi_response)
        
        try:
            json = eval(json[0])
            self.__token = json['data']['token']
            codeString = json['data']['codeString']
        except Exception:
            utils.show_msg('错误：Can\'t get passport getapi\'s response json.')
            return 0
        
        # logincheck
        passport_logincheck_url = passport_url + 'logincheck&&token='
        passport_logincheck_url += self.__token
        passport_logincheck_url += '&tpl=netdisk&apiver=v3&tt='
        passport_logincheck_url += utils.get_time()
        passport_logincheck_url += '&username='
        passport_logincheck_url += username
        passport_logincheck_url += '&isphone=false&callback=bd__cbs__q4ztud'
        passport_logincheck_response = self.get_response(passport_logincheck_url)

        json = utils.get_json_from_response(passport_logincheck_response)

        try:
            json = eval(json[0])
            codeString = json['data']['codeString']
            
        except Exception:
            utils.show_msg('错误:Can\'t get passport logincheck\'s response json.')
            return 0
        
        return codeString
        
    def login(self, username, password):
        '''
        进行登陆
        
        可能会弹出窗口输入验证码
        
        Args:
            username:用户名
            password:密码
        Returns:
            result:True为成功，False为失败或发生错误
        '''
        
        codestring = self.check_login(username)
        retry = 0
        
        while retry <= max_retry_times:
            if codestring == 0:
                return False
            
            if codestring is None:
                utils.show_msg('错误:codestring is None.')
                return False
        
            if codestring != '':
                # 验证码
                verifycode_img_url = captcha_url + codestring;
                verifycode_img_response = self.get_response(verifycode_img_url, html=False)
                verifycode_img_bytes = io.BytesIO(verifycode_img_response) 
                verifycode_img = Image.open(verifycode_img_bytes)
                verifycode_img.show()
                captch = raw_input("Enter verifycode：")
                verifycode_img.close()
            else:
                captch = ''
                
            post_data = {"staticpage": "http://pan.baidu.com/res/static/thirdparty/pass_v3_jump.html",
                        "charset": "utf-8",
                        "token": self.__token,
                        "tpl": "netdisk",
                        "subpro": "",
                        "apiver": "v3",
                        "tt": utils.get_time(),
                        "codestring": codestring,
                        "safeflg": "0",
                        "u": "http://pan.baidu.com/",
                        "isPhone": "",
                        "quick_user": "0",
                        "logintype": "basicLogin",
                        "logLoginType": "pc_loginBasic",
                        "idc": "",
                        "loginmerge": "true",
                        "username": username,
                        "password": password,
                        "verifycode": captch,  # 验证码
                        "mem_pass": "on",
                        "rsakey": "",
                        "crypttype": "",
                        "ppui_logintime": "2602",
                        "callback": "parent.bd__pcbs__msdlhs"
                        }
            passport_logincheck_response = self.get_response(passport_url + 'login', post_data)
            
            # 访问一次跳转地址和首页
            try:
                tmp = re.findall('decodeURIComponent\(\"([\s\S]*?)\"\)', passport_logincheck_response)
                jump_url = tmp[0]
                jump_url = jump_url.replace('\\', '')
                tmp = re.findall('accounts\s*?=\s*?\'([\s\S]*?)\'', passport_logincheck_response)
                account = tmp[0]
                jump_url += '?'
                tmp = re.findall('href\s*?\+=\s*?"([\s\S]*?)"', passport_logincheck_response)
                jump_url += tmp[0]
                jump_url += account
                self.get_response(jump_url)
                self.get_response(disk_home_url)
                
            except Exception:
                utils.show_msg('错误:Can\'t go to jump page.')
                return False
            
            # 错误处理
            try:
                tmp = re.findall('err_no=([-]?\d*)', jump_url)
                errno = tmp[0]
            except Exception:
                utils.show_msg('错误:Can\'t get check login error number.')
                return False
            
            if errno == '3' or errno == '6' or errno == '257' or errno == '200010':
                # 验证码错误，需要重新输入
                try:
                    tmp = re.findall('&codestring=([\s\S]*?)[&]?', jump_url)
                    codestring = tmp[0]
                    
                except Exception:
                    utils.show_msg('错误:Can\'t get codestring after error:' + errno +'.')
                    return False
                retry += 1
                
            elif errno == '0' or errno == '18' or errno == '400032' or errno == '400034' or errno == '400037' or errno == '400401':
                # 登陆成功
                return True
            
            elif errno == '120019' or errno == '120021':
                # 在弹出窗口操作
                try:
                    tmp = re.findall('&authtoken=([\s\S]*?)[&]?', jump_url)
                    authtoken = tmp[0]
                    tmp = re.findall('&gotourl=([\s\S]*?)[&]?', jump_url)
                    gotourl = tmp[0]
                    
                except Exception:
                    utils.show_msg('错误:Can\'t get authtoken and gotourl.')
                    return False
                '''
                此错误无法模拟，暂时不作处理
                '''
                utils.show_msg('目前由于此错误无法模拟，暂时不作处理，如知如何重现，请联系作者')
                return False
            
            utils.show_msg('错误:登陆错误，请重新尝试，错误代码：' + errno + '，错误信息：' + errmsg.get_login_errmsg(errno))
        
        utils.show_msg('错误:超出最大重试次数：' + str(max_retry_times))
        return False
        
    def logout(self):
        '''
        退出登陆
        
        Returns:
            result:True为成功，False为失败或发生错误
        '''
        
        passport_logout_response = self.get_response(logout_url)
        check_logout = re.findall('立即注册', passport_logout_response)
        if len(check_logout) > 0:
            return True
        else:
            return False
    
    def do_pan_api(self, api, args):
        '''
        执行百度网盘api
        
        Args:
            api:需要执行的api
            args:string格式参数
        Returns:
            结果True or False
        '''
        api_url = pan_api_url + api + '?'
        api_url += 'channel=chunlei&clienttype=0&web=1&t='
        api_url += utils.get_time()
        api_url += '&bdstoken=' + self.__token
        api_url += args
            
        pan_api_response = self.get_response(api_url)
        
        json = pan_api_response

        try:
            json = eval(json)
            errno = str(json['errno'])

            if errno == '0':
                return json['list']
        except Exception:
            utils.show_msg("错误:Can't get pan api:" + api + " response json.")
            return False
        
        # 错误处理
        utils.show_msg('错误:执行百度云api：' + api + '时出错，错误代码：' + errno + '，错误信息：' + errmsg.get_errmsg_by_errno(errno))
        return False
    
    def get_list(self, page='', page_size=''):
        '''
        获取目录列表，默认全部获取
        
        注意输入必须全是string格式
        
        Args:
            page：第几页
            page_size：每页几条记录，默认20
        Returns:
            dict格式文件信息
        '''
        
        args = ''
        if page != '':
            args += '&page=' + page
        if page_size != '':
            args += '&num=' + page_size
            
        return self.do_pan_api('list', args)
        