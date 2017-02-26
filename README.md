## BaiduCloudHelper

[![Licence](https://img.shields.io/badge/licence-MIT-blue.svg)](https://github.com/yp05327/BaiduCloudHelper/LICENSE) [![Python](https://img.shields.io/badge/python-2.7-blue.svg)](https://travis-ci.org/yp05327/BaiduCloudHelper) [![Python](https://travis-ci.org/yp05327/BaiduCloudHelper.svg?branch=master)]()

# 说明
本项目部分原理根据：[BaiduPCS](https://github.com/GangZhuo/BaiduPCS)改写而来，原项目使用C语言编写，人生苦短，我用python。  
百度网盘下载工具,目前开发中，主要开发环境为python2.7，多线程下载目前不支持python3.x（有一个很让人头痛的bug，在2.7中却能完美运行），其余功能均支持

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
``` 
  
安装依赖库，使用pip，Linux、Mac非root需要添加sudo  
  
```shell
pip install -r requirements.txt
``` 

# 使用
```shell
python main.py
```

# 目前支持功能
* 登陆、退出
* 获取文件列表
* 多线程下载（ide debug中有效）
* 图形界面（开发中）

# 目前已知问题
* 中文验证码无法识别
* 命令行模式无法进行多线程下载
* python3.x中多线程无法使用