## BaiduCloudHelper

[![Licence](https://img.shields.io/badge/licence-MIT-blue.svg)](https://github.com/yp05327/BaiduCloudHelper/LICENSE) [![Python](https://img.shields.io/badge/python-2.7%2C3.x-blue.svg)](https://travis-ci.org/yp05327/BaiduCloudHelper) [![Python](https://travis-ci.org/yp05327/BaiduCloudHelper.svg?branch=master)]()

# 说明
本项目部分原理根据：[BaiduPCS](https://github.com/GangZhuo/BaiduPCS)改写而来，原项目使用C语言编写，人生苦短，我用python。  
百度网盘下载工具,目前开发中，优先支持运行环境：python2.7 + Mac OS 10.12（开发环境）  
目前使用方法比较麻烦，窗口界面开发完成后即可解除封印  
目前仅测试了Mac OS下的情况，Windows问题将会在开发完成后解决

# Mac OS注意事项
Mac下使用window界面无法输入中文，需要前往[Activetcl](https://www.python.org/download/mac/tcltk/)下载对应Mac OS版本的Activetcl，并且需要升级python到2.7.13，升级方法直接从官网下载安装包并安装，然后运行时使用：  
```shell
python2.7 main.py
```

同时安装依赖库时也需要添加2.7标签：
```shell
pip2.7 install -r requirements.txt
```

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
命令行：  
打开main.py输入相关信息：

```python
username = '' # 用户名
password = '' # 密码
disk_file = '' # 网盘文件目录，格式：/文件夹/文件夹/文件名  或者  /文件名
download_file = '' # 下载到哪里，需要绝对路径
```

然后：  

```shell
python main.py
```
  
窗口（开发中，功能不全）：
```shell
python main.py -w
```

# 目前支持功能
* 登陆、退出
* 获取文件列表（只拿了个返回值，还不能显示）
* 多线程下载
* 图形界面（开发中）

# 目前已知问题
* 中文验证码无法识别