## BaiduCloudHelper

[![Licence](https://img.shields.io/badge/licence-MIT-blue.svg)](https://github.com/yp05327/BaiduCloudHelper/LICENSE) [![Python](https://img.shields.io/badge/python-2.7%2C3.3+-blue.svg)](https://github.com/yp05327/BaiduCloudHelper#) [![Python](https://travis-ci.org/yp05327/BaiduCloudHelper.svg?branch=master)](https://travis-ci.org/yp05327/BaiduCloudHelper)

# 说明
本项目百度云引擎原理根据：[BaiduPCS](https://github.com/GangZhuo/BaiduPCS)改写而来，原项目使用C语言编写，人生苦短，我用python。  
部分关键技术参考了：[baidupcsapi](https://github.com/ly0/baidupcsapi)
此外直链功能为抓包后提取的链接，因此是模拟百度网盘客户端的通信制作的  
目前开发中，优先支持运行环境：python2.7/3.6 + Mac OS 10.12（开发环境）  
目前仅测试了Mac OS下的情况，Windows问题将会在开发完成后解决  

# 更新记录
[点击此处](https://github.com/yp05327/BaiduCloudHelper/blob/master/update.md)

# 注意事项
* 直链获取会自动申请免费加速，如果没有免费加速时间则获取到的是普通连接（目前暂时是百度云客户端链接中取第一个）  
* 目前可以自动登录了，如果需要删除自动登录信息，请手动删除安装目录下的cookie.list文件  
* 命令行模式主要用于开发调试，不适合用户使用，请使用网页模式运行  
* 请勿输入非法变量或在公共网络使用，后果自负  
其次由于蛋疼的编码问题，本人技术有限，使用了eval函数，且未做大量的严格输入检测，因此具有一定的安全风险）  
* 请勿频繁开始任务暂停任务，在快下载完的时候会报很多错（由于python坑爹的多线程，暂停之后他还会继续跑一会，所以根本停不下来23333），但是下载的文件是没有问题的  
* 可以在webserver.py中第13行设置你需要的下载线程数量（修改thread_num数值大小），和下载速度之间有关系，直链有连接数限制，所以最高设置为120（本人测试结果），否则会报错。  
同时在downloadengine.py中找到：self.delta_range = 1024 * 1024 * 10 来设置区块大小，也会对速度产生影响，而且可能也会对暂停（每个线程在下载完一个区块之前不会停止）  
产生影响，请参考每个线程需要下载的时间，来设置合理大小，之后会在web界面中加入设置选项。  
线程数与区块大小应成反比，具体设置需要参照电脑配置、下载文件大小等进行灵活调整，就可以达到最优下载速度  
* 重新启动后，已完成任务会自动从下载列表中移除  
* 不要随意修改task.list文件，可能会导致下载进度无法读取的情况，然后可能就GG了  

# 目前支持功能
web模式（开发中）：
* (自动)登陆、退出
* 显示网盘文件
* 多线程下载文件
* 暂停下载

命令行：
* 仅限开发者功能调试

# 目前已知问题
下载中退出程序，再次打开，未下载完的任务会显示正在下载中，需要手动暂停，之后再启动
多线程下载器可能会出现文件数据错误的问题

# 安装
运行环境需要python，目前支持的python版本：

```
python2.7
python3.3+
```

安装依赖库，使用pip，Linux、Mac非root需要添加sudo

```shell
pip install -r requirements.txt
```

# 使用

web模式：

运行

```shell
python main.py -w
```

打开浏览器，访问：127.0.0.1:8000

系统信息会显示在右上角，不过出错了还是看一下控制台比较好

命令行（仅限开发者调试功能使用）：

打开main.py输入相关信息：

```python
username = '' # 用户名
password = '' # 密码
disk_file = '' # 网盘文件目录，格式：/文件夹/文件夹/文件名  或者  /文件名
file_name = '' # 文件名，为了方便就没有写从disk_file读取文件名
download_file = '' # 下载到哪里，需要绝对路径
```

然后运行：

```shell
python main.py
```
