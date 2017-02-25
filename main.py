# coding=utf-8
from baiducloudengine import BaiduCloudEngine
import utils
username = ''
password = ''

user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
#user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

def test(bdce):
    print(bdce.get_list())
    
def main():
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
        
if __name__ == "__main__":
    main()