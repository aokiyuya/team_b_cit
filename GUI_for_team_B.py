#! !(which python) # coding: utf-8
############################
# Author: Yuya Aoki
#
###########################
from logging import getLogger, basicConfig, DEBUG, StreamHandler
# from threading import Thread
# from datetime import datetime as dt
# import os
import re
import threading
import datetime
import socket
import atexit
import sys
import subprocess
# import time
from kivy.app import App
from kivy.uix.button import Button, Label
from kivy.uix.image import Image
from kivy.config import Config
from kivy.uix.actionbar import ActionBar, ActionButton
from kivy.uix.actionbar import ActionView, ActionPrevious
# from kivy.uix.textinput import TextInput
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
from kivy.uix.floatlayout import FloatLayout
# from kivy.core.image import Image as CoreImage
# from kivy.uix.scatter import Scatter

# 日本語扱う設定
resource_add_path('~/')
LabelBase.register(DEFAULT_FONT, '/Users/aoki/ipaexm.ttf')

# Window sizeの設定
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '400')

# print は使わず logger を使う
basicConfig(level=DEBUG)
logger = getLogger(__name__)
ch = StreamHandler()
logger.addHandler(ch)
ch.setLevel(DEBUG)
logger.info("info")
logger.debug("debug")
logger.warning("warning")
logger.error("error")

STRING = 0
IWATA_KANA = 1
SAY_SPEED = 100

THRESHOLD = 1


# open jtalk を立ち上げておく
class Openjtalk_straight(object):
    def __init__(self):
        self.start_openjtalk()

    def start_openjtalk(self):
        cmd = ['/usr/local/open_jtalk-1.08-straight-3.0.0/bin/'
               + 'run_open_jtalk.sh',
               '--',
               '-i',
               'iwata_kana',
               '-op',
               '-p',
               str(SAY_SPEED)]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def terminate(self):
        self.p.terminate()

    def change_speed_jtalk(self, speed):
        global SAY_SPEED
        self.p.terminate()
        SAY_SPEED = SAY_SPEED + speed
        logger.info(SAY_SPEED)
        cmd = ['/usr/local/open_jtalk-1.08-straight-3.0.0/bin/'
               + 'run_open_jtalk.sh',
               '--',
               '-i',
               'iwata_kana',
               '-op',
               '-p',
               str(SAY_SPEED)]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def talk(self, string):
        self.p.stdin.write(string.encode('utf-8'))
        self.p.stdin.flush()


# ログを保存
def write_dialogue(string):
    """This is function to write log"""
    NOW = str(datetime.datetime.now())
    with open('log.txt', 'a') as f:
        f.writelines(string + ', ' + NOW + '\n')


def at_exit():
    # print('\nExit')
    logger.info('exit')
    openjtalk.terminate()
    sys.exit(0)


def output(args):
    global output_label
    if 'Error' not in args:
        NOW = str(datetime.datetime.now())
        output_label.text = args + ' ' + NOW
    else:
        output_label.text = args
    output_label.texture_update()


def speak_with_iwata_kana(string):
    input_string = string
    if '\n' not in string:
        input_string = string + '\n'
    openjtalk.talk(input_string)


# 別スレッドで発話
# なにもない場合は呼び出さない
def speak_parallel(arg_string):
    if arg_string == '':
        return 0
    threading.Thread(target=say_command, args=(arg_string, )).start()


# 音声合成を行う．
def say_command(arg_string):
    # write_dialogue('say ' + arg_string)
    speak_with_iwata_kana(arg_string)
    output('said')


def command():
    output('command')


# kivyで日本語入力がうまくいかないので急遽作成
def speak_read():
    read_lines = ''
    while True:
        read_line = input()
        if read_line != '':
            write_dialogue(read_line)
        if 'clear' in read_line:
            read_line, read_lines = '', ''
            continue
        elif 'exit' in read_line:
            exit(0)
        read_lines += read_line
        if ';' in read_line:
            write_dialogue('say ' + read_lines.replace(';', '') + '\n')
            say_command(read_lines.replace(';', '') + '\n')
            output('said')
            read_lines = ''
        # print(read_lines, end='')


class MyActionBar():
    def __init__(self):

        actionview = ActionView()
        actionview.use_separator = True
        ap = ActionPrevious(title='Action', with_previous=False)
        actionview.add_widget(ap)
        self.command = ActionButton(text='command')
        self.command.bind(on_press=self.ActionCallback_command)
        actionview.add_widget(self.command)

        self.actionbar = ActionBar()
        self.actionbar.add_widget(actionview)

    def ActionCallback_exit(self, instance):
        exit(0)

    def ActionCallback_command(self, instance):
        command()


# 上下に設置したいが上手くいかないので宣言するだけ
# 多分一生使わない予感
class TalkBar():
    def __init__(self):
        actionview = ActionView()
        actionview.use_separator = True
        ap = ActionPrevious(title='Talk Action', with_previous=False)
        actionview.add_widget(ap)
        self.actionbar = ActionBar()
        self.actionbar.add_widget(actionview)


class RootWidget(FloatLayout):
    # ベタがきで汚いのでいつかkv langに移行する(しない)
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        # self.cols = 3
        global picture_list
        picture_list.append(Image(
            source='./al.png',
            size_hint=(.4, .4),
            pos_hint={'center_x': .5, 'center_y': .6}
        ))
        picture_list.append(Image(
            source='./TOFU_notlogo.png',
            size_hint=(.4, .4),
            pos_hint={'center_x': .5, 'center_y': .6}
        ))
        picture_list.append(Image(
            source='./TOFU_notlogo_2.png',
            size_hint=(.4, .4),
            pos_hint={'center_x': .5, 'center_y': .6}
        ))
        self.picture = picture_list[0]
        threading.Thread(target=self.make_server).start()
        self.build()

    def build(self):
        global output_label, picture_list
        # self.picture.reload()
        self.clear_widgets()
        self.add_widget(self.picture)
        self.A = Button(
            text='具材1',
            size_hint=(.2, .08),
            font_size=35,
            pos_hint={'center_x': .3, 'center_y': .3}
        )
        self.A.bind(on_press=self.on_click_A)
        self.add_widget(self.A)

        self.B = Button(
            text='具材2',
            size_hint=(.2, .08),
            font_size=35,
            pos_hint={'center_x': .5, 'center_y': .3}
        )
        self.B.bind(on_press=self.on_click_B)
        self.add_widget(self.B)

        self.C = Button(
            text='具材3',
            font_size=35,
            size_hint=(.2, .08),
            pos_hint={'center_x': .7, 'center_y': .3}
        )
        self.C.bind(on_press=self.on_click_C)
        self.add_widget(self.C)

        # change motor angle

        output_label = Label(
            text='no out put',
            size_hint=(.3, .08),
            font_size=25,
            pos_hint={'center_x': .3, 'center_y': .1}
        )
        self.add_widget(output_label)

        # self.action_bar = MyActionBar()

        # self.add_widget(self.action_bar.actionbar)

    def on_click_A(self, instance):
        self.picture_reload(0)
        output('click')

    def on_click_B(self, instance):
        self.picture_reload(1)
        output('click')

    def on_click_C(self, instance):
        self.picture_reload(2)
        output('click')

    def make_server(self, host='', port=39400):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sp:
            sp.bind((host, port))
            sp.listen(2)
            while server_is_running:
                data_str = ''
                client_socket, address = sp.accept()
                while True:
                    # 深い意味はない
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    data_str = data_str + data.decode('utf-8')
                print(data_str)
                client_socket.close()
                if re.match(r'[あ-ん一-龥0-9]', data_str):
                    global user_state
                    user_state = 'finish'
                    if re.match(r'[1一]', data_str):
                        self.picture_reload(0)
                    if re.match(r'[2二]', data_str):
                        self.picture_reload(1)
                    if re.match(r'[3三]', data_str):
                        self.picture_reload(2)
                else:
                    pass

    def picture_reload(self, num):
        global picture_list
        # self.picture = Image(
        self.picture = picture_list[num]
        # picture_list.source = source_file
        # self.picture.reload()
        self.build()


class TestApp(App):
    def __init__(self):
        App.__init__(self)

    def build(self):
        self.root = RootWidget()
        self.title = 'cit_team_B'
        self.icon = 'al.png'
        return self.root


# ユーザが何を言ったかを受け取って処理する部分．
class Dialog_manager():
    def __init__(self):
        self.user_speak = ''

    def set_user_speak(self, string):
        print(string)
        self.user_speak = "".join(string)
        if 'こん' in self.user_speak:
            say_command('こんにちは')


# 名前空間を汚すので基本は main 関数を作ってあげる
def main():
    # threading.Thread(target=speak_read).start()
    atexit.register(at_exit)
    testApp.run()


if __name__ == '__main__':
    server_is_running = True
    user_state = None
    dialog_flag = True
    openjtalk = Openjtalk_straight()
    picture_list = []
    testApp = TestApp()
    main()

# vim:set foldmethod=marker:
