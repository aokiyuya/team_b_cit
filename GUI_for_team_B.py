#! !(which python)
# coding: utf-8
###########################
# Author: Yuya Aoki
#
###########################
from kivy.app import App
from kivy.uix.button import Button, Label
from kivy.config import Config
from kivy.uix.actionbar import ActionBar, ActionButton
from kivy.uix.actionbar import ActionView, ActionPrevious
# , ActionGroup
from kivy.uix.textinput import TextInput
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
# from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.stacklayout import StackLayout
# import kivy.clock
import os
import re
import threading
import datetime
import socket
import atexit
import sys
import subprocess
import time


# HOST = '192.168.8.102'    # The remote host
HOST = '192.168.3.88'    # The remote host
PORT = 2828              # The same port as used by the server

# 日本語扱う設定
resource_add_path("./")
LabelBase.register(DEFAULT_FONT, "ipaexm.ttf")

# Window sizeの設定
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '400')

STRING = 0
IWATA_KANA = 1
SAY_SPEED = 100

# open jtalk を立ち上げておく
cmd = ['/usr/local/open_jtalk-1.08-STRAIGHT-3.0.0/bin/run_open_jtalk.sh',
       '--',
       '-i',
       'iwata_kana',
       '-op',
       '-p',
       str(SAY_SPEED)]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

cmd = ['/usr/local/open_jtalk-1.08-STRAIGHT-3.0.0/bin/run_open_jtalk.sh',
       '--',
       '-op',
       '-p',
       str(SAY_SPEED)]

speak_stdin_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

def change_speed_jtalk(speed):
    global p, SAY_SPEED, speak_stdin_proc
    p.terminate()
    SAY_SPEED = SAY_SPEED + speed
    cmd = ['/usr/local/open_jtalk-1.08-straight-3.0.0/bin/run_open_jtalk.sh',
           '--',
           '-i',
           'iwata_kana',
           '-op',
           '-p',
           str(SAY_SPEED)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cmd = ['/usr/local/open_jtalk-1.08-STRAIGHT-3.0.0/bin/run_open_jtalk.sh',
           '--',
           '-op',
           '-p',
           str(SAY_SPEED)]
    speak_stdin_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)


# ログを保存
def write_dialogue(string):
    """This is function to write log"""
    NOW = str(datetime.datetime.now())
    with open('log.txt', 'a') as f:
        f.writelines(string + ', ' + NOW + '\n')


# def send_command(command):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.connect((HOST, PORT))
#         s.sendall(command.encode('utf-8'))
#     write_dialogue(command)


def at_exit():
    print("\nExit")
    # send_command('exit')
    p.terminate()
    speak_stdin_proc.terminate()
    sys.exit(0)


def output(args):
    global output_label
    if 'Error' not in args:
        NOW = str(datetime.datetime.now())
        output_label.text = args + " " + NOW
    else:
        output_label.text = args
    output_label.texture_update()


def speak_with_iwata_kana(string):
    p.stdin.write(string.encode('utf-8'))
    p.stdin.flush()


# 岩田カナ文でない文章を音声合成
def speak_jtalk(string):
    speak_stdin_proc.stdin.write(string.encode('utf-8'))
    speak_stdin_proc.stdin.flush()


# 別スレッドで発話
# なにもない場合は呼び出さない
def speak_parallel(arg_string):
    if arg_string == '':
        return 0
    threading.Thread(target=say_command, args=(arg_string, )).start()


# 音声合成を行う．
def say_command(arg_string):
    write_dialogue('say ' + arg_string)
    speak_with_iwata_kana(arg_string)
    output('said')


def command():
    output("command")

# kivyで日本語入力がうまくいかないので急遽作成
def speak_read():
    read_lines = ''
    while True:
        read_line = input()
        if read_line != "":
            write_dialogue(read_line)
        if 'clear' in read_line:
            read_line, read_lines = '', ''
            continue
        elif 'exit' in read_line:
            exit(0)
        elif 'change' in read_line:
            change_speed_jtalk(int(read_line.split(' ')[1]))
        read_lines += read_line
        if ';' in read_line:
            write_dialogue('say ' + read_lines.replace(';', '') + '\n')
            speak_jtalk(read_lines.replace(';', '') + '\n')
            output('said')
            read_lines = ''
        print(read_lines, end='')


class MyActionBar():
    def __init__(self):

        actionview = ActionView()
        actionview.use_separator = True
        ap = ActionPrevious(title='Action', with_previous=False)
        actionview.add_widget(ap)
        self.command = ActionButton(text="command")
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
        global output_label
        super(RootWidget, self).__init__(**kwargs)
        # self.cols = 3
        self.A = Button(
            text="具材A",
            size_hint=(.2, .08),
            font_size=35,
            pos_hint={'center_x': .4, 'center_y': .3}
        )
        self.A.bind(on_press=self.on_click_A)
        self.add_widget(self.A)

        self.B = Button(
            text="具材B",
            size_hint=(.2, .08),
            font_size=35,
            pos_hint={'center_x': .6, 'center_y': .3}
        )
        self.B.bind(on_press=self.on_click_B)
        self.add_widget(self.B)

        self.C = Button(
            text="具材C",
            font_size=35,
            size_hint=(.2, .08),
            pos_hint={'center_x': .8, 'center_y': .3}
        )
        self.C.bind(on_press=self.on_click_C)
        self.add_widget(self.C)

        # change motor angle

        output_label = Label(
                text="no out put",
                size_hint=(.3, .08),
                font_size=25,
                pos_hint={'center_x': .7, 'center_y': .1}
            )
        self.add_widget(output_label)

        self.action_bar = MyActionBar()

        self.add_widget(self.action_bar.actionbar)


    def on_click_A(self, instance):
        pass

    def on_click_B(self, instance):
        pass

    def on_click_C(self, instance):
        pass

class TestApp(App):
    def __init__(self):
        App.__init__(self)

    def build(self):
        # self.root = root = RootWidget()
        self.root = RootWidget()
        self.title = 'cit_team_B'
        self.icon = 'al.png'
        return self.root


if __name__ == '__main__':
    threading.Thread(target=speak_read).start()
    atexit.register(at_exit)
    TestApp().run()


# vim:set foldmethod=marker:
