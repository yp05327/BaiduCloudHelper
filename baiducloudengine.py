# coding=utf-8
import urllib
import urllib2
import cookielib
import utils
import re

from PIL import Image

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
disk_home_url = 'http://pan.baidu.com/disk/home'
passport_url = 'https://passport.baidu.com/v2/api/?'
get_public_key_url = 'https://passport.baidu.com/v2/getpublickey?'
logout_url = 'https://passport.baidu.com/?logout&u=http://pan.baidu.com'
captcha_url = 'https://passport.baidu.com/cgi-bin/genimage?'

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
        
    def get_response(self, url, post_data=None):
        '''
        获取http返回内容
        
        Args:
            url:地址
            post_data:post数据，默认为None
        Returns:
            http返回内容
        '''
        
        if post_data is not None:
            post_data = urllib.urlencode(post_data)
            
        req = urllib2.Request(url, data=post_data, headers=self.__headers)
        response = self.__opener.open(req)
        content = response.read()
        
        encoding = response.info().get('Content-Encoding')
        if encoding == 'gzip':
            content = utils.gzip_decode(content)
        elif encoding == 'deflate':
            content = utils.deflate_decode(content)
        
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
            print "Get passport getapi's response json error."
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
            print "Error:Can't get passport logincheck's response json."
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
        
        if codestring == 0:
            return False
        
        if codestring is None:
            print "Error:codestring is None."
            return False
        
        if codestring != '':
            # 验证码
            verifycode_img_url = captcha_url + codestring;
            verifycode_img_code = self.get_response(verifycode_img_url)
            verifycode_img = Image.open(verifycode_img_code)
            verifycode_img.show()
            captch = raw_input("Enter verifycode：");
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
        
        '''
        此处需要进行错误处理，暂时跳过
        
        
        '''
        
        # 访问一次跳转地址
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
        except Exception:
            print 'Error:Can\'t go to jump page.'
            return False
        
        return True
    
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
        