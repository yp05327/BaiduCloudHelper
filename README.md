## BaiduCloudHelper

[![Licence](https://img.shields.io/badge/licence-MIT-blue.svg)](https://github.com/yp05327/BaiduCloudHelper/LICENSE) [![Python](https://img.shields.io/badge/python-2.7%2C3.x-blue.svg)](https://travis-ci.org/yp05327/BaiduCloudHelper) [![Python](https://travis-ci.org/yp05327/BaiduCloudHelper.svg?branch=master)]()

# 说明
本项目部分原理根据：[BaiduPCS](https://github.com/GangZhuo/BaiduPCS)改写而来，原项目使用C语言编写，人生苦短，我用python。  
百度网盘下载工具,目前开发中，优先支持运行环境：python2.7 + Mac OS 10.12（开发环境）  
目前使用方法比较麻烦，网页界面开发完成后即可解除封印  
目前仅测试了Mac OS下的情况，Windows问题将会在开发完成后解决  

# 注意事项
* 每次开启都需要登陆，不会保存账号的cookies（目前测试情况，保存了之后，重新读取进行下载会出现403，所以保存了也没卵用）
* 请勿输入非法变量或在公共网络使用，后果自负（首先密码为明文传输，其次由于蛋疼的编码问题，本人技术有限，使用了eval函数，此函数具有一定的安全风险）

# 安装
运行环境需要python，目前支持的python版本：  
  
```
python2.7  
python3.x
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

命令行：

打开main.py输入相关信息：

```python
username = '' # 用户名
password = '' # 密码
disk_file = '' # 网盘文件目录，格式：/文件夹/文件夹/文件名  或者  /文件名
download_file = '' # 下载到哪里，需要绝对路径
```

然后运行：

```shell
python main.py
```
# 目前支持功能
命令行（或将只支持以下功能）：
* 登陆、退出
* 多线程下载

web模式（开发中）：
* 登陆、退出
* 显示网盘文件

# 目前已知问题
* 中文验证码无法识别（不知道为什么），所以请勿在非常用ip下进行登陆以及频繁登陆
