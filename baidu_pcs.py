# coding=utf-8
from baiducloudengine import BaiduCloudEngine

username = ''
password = ''

user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
#user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

def main():
    bdce = BaiduCloudEngine()
    if bdce.login(username, password):
        print 'login success'
    else:
        print 'login failed'
        return 0
    
    if bdce.logout():
        print 'logout success'
    else:
        print 'logout failed'
        return 0
        
if __name__ == "__main__":
    main()