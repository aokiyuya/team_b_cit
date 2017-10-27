#! !(which python)
# coding: utf-8
###########################
# Author: Yuya Aoki
#
###########################
from logging import getLogger, basicConfig, DEBUG, StreamHandler
from threading import Thread
from datetime import datetime as dt
import os
import re
import threading
import datetime
import socket
import atexit
import sys
import subprocess
import time
import xml.sax
import xml.sax.handler
from kivy.app import App
from kivy.uix.button import Button, Label
from kivy.uix.image import Image
from kivy.config import Config
from kivy.uix.actionbar import ActionBar, ActionButton
from kivy.uix.actionbar import ActionView, ActionPrevious
from kivy.uix.textinput import TextInput
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
from kivy.uix.floatlayout import FloatLayout
from kivy.core.image import Image as CoreImage
from kivy.uix.scatter import Scatter

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


def at_exit():
    # print('\nExit')
    logger.info('exit')
    p.terminate()
    speak_stdin_proc.terminate()
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
    p.stdin.write(input_string.encode('utf-8'))
    p.stdin.flush()


# 岩田カナ文でない文章を音声合成
def speak_jtalk(string):
    input_string = string
    if '\n' not in string:
        input_string = string + '\n'
    speak_stdin_proc.stdin.write(input_string.encode('utf-8'))
    speak_stdin_proc.stdin.flush()


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
        elif 'change' in read_line:
            change_speed_jtalk(int(read_line.split(' ')[1]))
        read_lines += read_line
        if ';' in read_line:
            write_dialogue('say ' + read_lines.replace(';', '') + '\n')
            speak_jtalk(read_lines.replace(';', '') + '\n')
            output('said')
            read_lines = ''
        # print(read_lines, end='')


class Picture(Scatter):
    source = './al.png'
    size_hint = .4, .4
    Image = {
        'id': 'image',
        'source': source
    }
    # pos_hint = (-36, -36)

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
        self.picture = Image(
            source='./al.png',
            size_hint=(.4, .4),
            pos_hint={'center_x': .5, 'center_y': .6}
        )
        self.build()

    def build(self):
        global output_label
        self.picture.reload()
        self.clear_widgets()
        self.add_widget(self.picture)
        self.A = Button(
            text='具材A',
            size_hint=(.2, .08),
            font_size=35,
            pos_hint={'center_x': .3, 'center_y': .3}
        )
        self.A.bind(on_press=self.on_click_A)
        self.add_widget(self.A)

        self.B = Button(
            text='具材B',
            size_hint=(.2, .08),
            font_size=35,
            pos_hint={'center_x': .5, 'center_y': .3}
        )
        self.B.bind(on_press=self.on_click_B)
        self.add_widget(self.B)

        self.C = Button(
            text='具材C',
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
        self.picture = Image(
            source='./TOFU_notlogo.png',
            size_hint=(.4, .4),
            pos_hint={'center_x': .5, 'center_y': .6}
        )
        self.build()

    def on_click_B(self, instance):
        self.picture = Image(
            source='./TOFU_notlogo_2.png',
            size_hint=(.4, .4),
            pos_hint={'center_x': .5, 'center_y': .6}
        )
        self.build()

    def on_click_C(self, instance):
        pass

class TestApp(App):
    def __init__(self):
        App.__init__(self)

    def build(self):
        self.root = RootWidget()
        self.title = 'cit_team_B'
        self.icon = 'al.png'
        return self.root


# ストリームをラッピングするクラス
class StreamWrapperForJulius(object):
    u"""Juliusの結果をSAXパーサが振る舞えるようにするためのラッパー"""

    def __init__(self, stream):
        u"""コンストラクタ"""
        # ストリーム
        self._stream = stream
        # ヘッダが読み込まれたかどうか
        self._header_is_read = 0

    def read(self, size):
        u"""ストリームから読み込みを行う．SAXパーサはこのメソッドだけ呼ぶ"""


        # ヘッダが読まれてなければヘッダを返す
        if self._header_is_read < 2:
            self._header_is_read += 1
            return '<ROOT>\n'

        # 要求されたサイズは無視して，１行分読み込む
        result = self._stream.readline()
        # '.' だけが入ってくる場合があるので，その場合はスキップする．
        while result == '.\n':
            result = self._stream.readline()
        # 空白はいらない．また，<s>と</s>は特別なキャラクタ'<', '>'を
        # 含んでいるので変換する
        result = result.strip()
        result = result.replace('<s>', '&lt;s&gt;')
        result = result.replace('</s>', '&lt;/s&gt;')
        return result

    def __getattr__(self, attr):
        # その他のメソッドを本物のストリームのメソッドにする
        return getattr(self._stream, attr)


# 終了要求受理を意味する例外クラス
class TerminateRequestedException(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)


# XMLハンドラ
class JuliusResultHandler(xml.sax.handler.ContentHandler):
    u"""Juliusの結果のハンドラ.

    コンストラクタに引数が与えられた場合，ParserThreadの
    オブジェクトであることを前提とする．
    _runningプロパティがFalseの際にstartElementメソッドは
    （正常終了を表す）TerminateRequestedExceptionを投げる．
    """

    def __init__(self, thread=None):
        self._thread = thread
        self.dialog_manager = Dialog_manager()
        self.startTime = dt.today()
        self.stopTime = dt.today()
        self.diff = dt.today()

    # 時間インスタンスをreturn
    def setStartTime(self):
        self.startTime = dt.today()
        logger.info('setStartTime')

    def setStopTime(self):
        global user_state
        self.stopTime = dt.today()
        logger.info('setStopTime')
        self.diff = self.stopTime - self.startTime
        logger.info('total_seconds:' + str(self.diff.total_seconds()))
        if self.diff.total_seconds() > THRESHOLD:
            user_state = 'finish'

        # 時間を文字列で出力
    def getTimeString(self, time):
        d = time
        logger.debug(d.strftime('%Y/%m/%d %H:%M:%S.%f'))
        return d.strftime('%Y/%m/%d %H:%M:%S.%f')


    def startElement(self, name, attrs):
            # 終了要求されている場合はTerminateRequestedExceptionを投げる
        if self._thread is not None and self._thread._running is False:
            raise TerminateRequestedException()
        if name == 'RECOGOUT':
            # 認識結果取得開始につき結果リストを初期化
            self._result = []
        elif name == 'SHYPO':
            # 文仮説取得開始につき文情報を初期化
            self._sentence = {'SCORE': float(attrs.getValue('SCORE')),
                                # 'GRAM':  attrs.getValue('GRAM'),
                                'WORDS': []}
        elif name == 'WHYPO':
            # 単語仮説取得につき文情報に単語を追加
            self._sentence['WORDS'].append(attrs.getValue('WORD'))
        elif name == 'STARTRECOG':
            self.setStartTime()
        elif name == 'ENDRECOG':
            self.setStopTime()

        elif name == 'SYSINFO':
            logger.info(attrs.get('PROCESS'))
        else:
            # その他は無視
            pass

    def endElement(self, name):
        if name == 'RECOGOUT':
            # 認識結果取得終了につき結果リストを表示
            prettyPrintJuliusRecogResult(self._result)
            # 認識結果を Dialog_manager に投げる
            self.dialog_manager.set_user_speak(self._result[0]['WORDS'])
        elif name == 'SHYPO':
            # 文仮説取得終了につき，結果を結果リストに追加
            self._result.append(self._sentence)

    def characters(self, content):
        # 文字列は無視
        pass


def prettyPrintJuliusRecogResult(result):
    u"""JuliusResultHandlerがまとめた認識結果を見やすく表示する"""
    logger.info('-----')
    for i, r in zip(range(len(result)), result):
        print(u'認識結果%d（スコア %f)' % (i + 1, r['SCORE']))
        print(u'  ' + ' '.join(r['WORDS']))
    logger.info('-----')


class ParserThread(Thread):
    u"""パーサを別スレッドで実行するためのスレッド"""

    def __init__(self, stream):
        u"""コンストラクタ"""
        super(ParserThread, self).__init__()
        # 実行ステータス．Falseの場合は次回のパージング時に例外で停止する
        self._running = True
        # パーサ実体
        self._parser = xml.sax.make_parser()
        # ハンドラ設定
        self._parser.setContentHandler(JuliusResultHandler(self))
        # ストリーム
        self._stream = stream

    def run(self):
        try:
            # パージング開始
            self._parser.parse(StreamWrapperForJulius(self._stream))
        except TerminateRequestedException:
            # 終了要求後に正常に終了したことを表すので単にreturnする
            return

    def terminate(self):
        u"""スレッドを停止する"""
        # 実行停止要求
        self._running = False
        # コマンドを投げて，その返答を受取ることによって
        # わざとパージングをすすめるトリック
        self._stream.write('STATUS\n')
        self._stream.flush()


# ユーザが何を言ったかを受け取って処理する部分．
class Dialog_manager():
    def __init__(self):
        self.user_speak = ''

    def set_user_speak(self, string):
        print(string)
        self.user_speak = "".join(string)
        if 'こん' in self.user_speak:
            speak_jtalk('こんにちは')


# 名前空間を汚すので基本は main 関数を作ってあげる
def main():
    threading.Thread(target=speak_read).start()

    # Juliusへの接続
    host = 'localhost'
    port = 10500
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    stream = sock.makefile()
    parserThread = ParserThread(stream)
    parserThread.start()

    atexit.register(at_exit)
    TestApp().run()


if __name__ == '__main__':
    main()

# vim:set foldmethod=marker:
