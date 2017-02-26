# coding=utf-8
import utils
import downloadengine
from baiducloudengine import BaiduCloudEngine

import traceback
import unicodedata

# 兼容2.7和3.x
try:
    import tkMessageBox
    import tkSimpleDialog
    from Tkinter import *
except ImportError:
    from tkinter import *
    import tkinter.messagebox as tkMessageBox
    import tkinter.simpledialog as tkSimpleDialog
    
from PIL import Image, ImageTk

class WindowEngine:
    def __init__(self, width=800, height=600):
        self.bdce = BaiduCloudEngine(window=self)
        downloadengine.window = self
        
        self.window = Tk()
        self.window.title('百度云下载工具')
        self.window.minsize(width, height)
        self.window.maxsize(width, height)
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width/2) - (width/2)   
        y = (screen_height/2) - (height/2)
        self.window.geometry('%dx%d+%d+%d' % (width, height, x, y))
        # 进入消息循环
        self.login_screen_items = {
            'Label': [{'name': 'username_label', 'args': {'text': '用户名'}, 'grid_args': {'row': 0}},
                      {'name': 'password_label', 'args': {'text': '密码'}, 'grid_args': {'row': 1}}],
            'Entry': [{'name': 'username_entry', 'args': {'width':14}, 'grid_args': {'row': 0, 'column': 1}},
                      {'name': 'password_entry', 'args': {'show': '*', 'width':14}, 'grid_args': {'row': 1, 'column': 1}}],
            'Button': [{'name': 'login_button', 'args': {'text': '登录', 'command': self.click_login_btn}, 'grid_args': {'row':4}}]
        }
        self.load_screen('login_screen', self.login_screen_items)
        self.window.mainloop()
    
    def load_screen(self, screen_name, items):
        self.screen_item_dict = {}
        
        try:
            for item in items:
                if item == 'Label':
                    for label in items[item]:
                        _label = Label(self.window, label['args'])
                        _label.grid(label['grid_args'])
                        self.screen_item_dict[label['name']] = _label
                elif item == 'Entry':
                    for entry in items[item]:
                        _entry = Entry(self.window, entry['args'])
                        _entry.grid(entry['grid_args'])
                        self.screen_item_dict[entry['name']] = _entry
                elif item == 'Button':
                    for button in items[item]:
                        _button = Button(self.window, button['args'])
                        _button.grid(button['grid_args'])
                        self.screen_item_dict[button['name']]= _button
                elif item == 'Listbox':
                    for listbox in items[item]:
                        _listbox = Listbox(self.window, listbox['args'])
                        _listbox.grid(listbox['grid_args'])
                        self.screen_item_dict[listbox['name']]= _listbox
                        
                        for file in listbox['insert']:
                            _listbox.insert(file['file'])
                            
            self.screen_name = screen_name
        except Exception:
            utils.show_msg('错误:加载界面：%s错误' % screen_name, self)
            utils.show_msg(traceback.print_exc())
    
    def destroy_screen(self):
        try:
            for item in self.screen_item_dict:
                self.screen_item_dict[item].destroy()
                
            self.screen_name = ''
        except Exception:
            utils.show_msg('错误:清除界面：%s错误' % self.screen_name, self)
            utils.show_msg(traceback.print_exc())
        
    def click_login_btn(self):
        username = self.screen_item_dict['username_entry'].get()
        password = self.screen_item_dict['password_entry'].get()
        
        if username == '' or password == '':
            utils.show_msg('请输入用户名和密码', self)
            return 0
        
        if self.bdce.login(username.encode('utf-8'), password.encode('utf-8')):
            # 登陆成功，加载界面
            self.destroy_screen()
            
            self.disk_home_items = {
                'Label': [{'name': 'username_label', 'args': {'text': '欢迎：' + username}, 'grid_args': {'row': 0}},
                          {'name': 'disk_label', 'args': {'text': '网盘容量：'}, 'grid_args': {'row': 1}},
                          {'name': 'info_label', 'args': {'text': '状态：获取文件目录'}, 'grid_args': {'row': 2}}],
                'Listbox': [{'name': 'file_list', 'insert': [{'file': '11'}, {'file': '22'}], 'args': {}, 'grid_args': {'row': 3, 'column': 0}}],
                'Button': [{'name': 'download_button', 'args': {'text': '下载', 'command': self.click_download_btn}, 'grid_args': {'row':4, 'column': 0}},
                           {'name': 'logout_button', 'args': {'text': '退出', 'command': self.click_logout_btn}, 'grid_args': {'row':4, 'column': 1}}]
            }
            self.load_screen('disk_home', self.disk_home_items)
            
            # 获取文件列表
            file_list = self.bdce.get_list('/')
            print(file_list)
        else:
            utils.show_msg('登录失败', self)
    
    def click_verifycode_btn(self):
        verifycode = self.screen_item_dict['verifycode_dialog_entry'].get().encode('utf-8')
        
        if verifycode == '':
            utils.show_msg('请输入验证码', self)
            return 0
        
        # 关闭窗口
        self.screen_item_dict['verifycode_dialog_label'].destroy()
        self.screen_item_dict['verifycode_dialog_entry'].destroy()
        self.screen_item_dict['verifycode_dialog_button'].destroy()
        self.screen_item_dict['verifycode_dialog'].destroy()
        
        self.verifycode = verifycode
    
    def click_download_btn(self):
        pass
        
    def click_logout_btn(self):
        if self.bdce.logout():
            self.destroy_screen()
            
            self.load_screen('login_screen', self.login_screen_items)
        else:
            utils.show_msg('退出失败，请重新登录', self)
            
    def show_verifycode_img(self, img):
        img = ImageTk.PhotoImage(img)
        
        dialog = Toplevel()
        dialog.title('请输入验证码')
        width = 350
        height = 100
        dialog.minsize(width, height)
        dialog.maxsize(width, height)
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width/2) - (width/2)   
        y = (screen_height/2) - (height/2)
        dialog.geometry('%dx%d+%d+%d' % (width, height, x, y))
        
        verifycode_dialog_label = Label(dialog, image=img)
        verifycode_dialog_entry = Entry(dialog)
        verifycode_dialog_button = Button(dialog, text='确定', command=self.click_verifycode_btn)
        
        verifycode_dialog_label.grid(row=0, column=0)
        verifycode_dialog_entry.grid(row=0, column=1)
        verifycode_dialog_button.grid(row=1)
        
        self.screen_item_dict['verifycode_dialog'] = dialog
        self.screen_item_dict['verifycode_dialog_label'] = verifycode_dialog_label
        self.screen_item_dict['verifycode_dialog_entry'] = verifycode_dialog_entry
        self.screen_item_dict['verifycode_dialog_button'] = verifycode_dialog_button
        
        # 这里很关键，否则就不是模态对话框了
        dialog.focus_set()
        dialog.grab_set()
        dialog.wait_window()
        
        try:
            if self.verifycode == '':
                utils.show_msg('错误：Get verifycode from dialog failed', self)
        except Exception:
            utils.show_msg('错误：Get verifycode failed', self)
            utils.show_msg(traceback.print_exc())
            
        return self.verifycode
        
    def show_msg(self, msg):
        tkMessageBox.showinfo("提示", msg)
        
    def quit(self):
        self.window.quit()