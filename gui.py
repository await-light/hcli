# TODO 外部 粗糙 完善消息渲染
# TODO 外部 添加不同颜色主题(包括字体选择,字体粗细,字体大小)
# TODO 外部 支持markdown
# TODO 外部 分辨普通文本和富文本
# TODO 内部 将一些常量添加到common.py

import sys
import json
import time
import queue

from PyQt5.Qt import *
from websocket import (create_connection,
                       WebSocket,
                       WebSocketConnectionClosedException)

import common
from common import Label
import debug_special
from captcha import string2png


class DEBUG:
    """
    调试用
    de: 参数列表
    debug_connection: 模拟WebSocket连接
    """
    de = {
        "show_window_size": False,  # 显示窗口大小在左上角
        "turn_to_chat_in_any_situation": True,  # 除去网络部分,直接登录
        "print_all_received_data": True,  # 输出所有接收到的消息
        "print_if_login_layout_widgets_destroyed": True  # 输出loginlayout(包括loginlayout)中的控件是否被销毁
    }
    debug_connection = debug_special.DebugWebSocket(received_message_list=[
        {"cmd": "onlineSet", "nicks": ["test1", "test2", "test3", "test4", "Ikun", "Ikun2", "Ikun3", "Ikun114514"]},
        {'cmd': 'chat', 'nick': 'dfs', 'uType': 'user', 'userid': 5045011596697, 'channel': 'your-channel',
         'text': 'hello', 'level': 100, 'time': 1691657928760},
        {'cmd': 'info', 'channel': 'your-channel', 'from': 'await', 'to': 5045011596697,
         'text': 'await whispered: fuck', 'type': 'whisper', 'trip': 'for9zT', 'level': 100, 'uType': 'user',
         'time': 1691657935276},
        {'cmd': 'emote', 'nick': 'await', 'userid': 6195602720136, 'text': '@await hello', 'channel': 'your-channel',
         'trip': 'for9zT', 'time': 1691657938958},
        {'cmd': 'chat', 'nick': 'await', 'uType': 'user', 'userid': 6195602720136, 'channel': 'your-channel',
         'text': 'awa', 'level': 100, 'trip': 'for9zT', 'time': 1691657942873},
        {'nick': 'await', 'trip': 'for9zT', 'uType': 'user', 'hash': 'gigSTBJd6hXecPZ', 'level': 100,
         'userid': 6195602720136, 'isBot': False, 'color': 'FF6000', 'cmd': 'updateUser', 'channel': 'your-channel',
         'time': 1691657953469},
        {'cmd': 'onlineAdd', 'nick': 'MelonFour__', 'trip': 'Myh1TA', 'uType': 'user', 'hash': 'HeecuxmRpb5kMBI',
         'level': 100, 'userid': 1607159521911, 'isBot': False, 'color': False, 'channel': 'your-channel',
         'time': 1691657967855},
        {'cmd': 'warn',
         'text': 'You are sending too much text. Wait a moment and try again.\nPr'
                 'ess the up arrow key to restore your last message.',
         'channel': 'your-channel', 'time': 1691658045130},
        {'cmd': 'warn', 'text': 'You are being rate-limited or blocked.', 'channel': 'your-channel',
         'time': 1691658071093},
        {'cmd': 'info',
         'text': "# All commands:\n|Category:|Name:|\n|---:|---|\n|Admin:|addmod, bomb, deletecmd, listusers, reload, r"
                 "emovemod, saveconfig, shout|\n|Core:|changecolor, changenick, chat, emote, help, invite, join, morest"
                 "ats, move, ping, session, stats, updateMessage, whisper|\n|Fun:|hax|\n|Internal:|disconnect, socketre"
                 "ply|\n|Mod:|anticmd, authtrip, ban, controltor, deauthtrip, disablecaptcha, dumb, enablecaptcha, forc"
                 "ecolor, kick, lockroom, moveuser, overflow, speak, unban, unbanall, unlockroom, uwuify|\n---\nFor spe"
                 "cific help on certain commands, use either:\nText: `/help <command name>`\nAPI: `{cmd: 'help', comman"
                 "d: '<command name>'}`",
         'channel': 'your-channel', 'time': 1691658156880},
        {'cmd': 'info', 'channel': 'your-channel', 'from': 5045011596697, 'to': 6195602720136,
         'text': 'You whispered to @await: hello', 'type': 'whisper', 'time': 1691658173163}
    ])


class QtHackchatPort(QThread):
    def __init__(self,
                 channel,
                 nick,
                 password,
                 signals_window,
                 signals_loginlayout):
        """
        hackchat的接口,用于收消息和发消息
        :param channel: 加入的频道
        :param nick: 名称
        :param password: 密码(可选)
        :param signals_window: window的所有信号
        :param signals_loginlayout: loginlayout的所有信号
        """
        super().__init__()
        self.channel = channel
        self.nick = nick
        self.password = password
        self.connection = None

        self.signals_window = signals_window
        self.signals_loginlayout = signals_loginlayout

    def _succeed_login(self, first_msg):
        """
        成功进入聊天室将会调用此函数
        :param first_msg: 第一条消息(onlineSet)
        :return:
        """
        print("enter the channel successfully")
        self.signals_window["signal_turn_to_layout_chat"].emit((self.connection, first_msg))

    def _recv_data(self):
        """
        返回收到的消息
        :return:
        """
        data = json.loads(self.connection.recv())
        if DEBUG.de["print_all_received_data"]:
            print(data)
        return data

    def send_data(self, json_: dict):
        """
        发送数据
        :param json_: json数据(格式:dict)
        :return: 成功为True, 失败为False
        """
        if self.connection is not None:
            self.connection.send(json.dumps(json_))
            return True
        return False

    def run(self):
        """
        使用QThread连接,防止程序卡顿
        :return:
        """
        if DEBUG.de["turn_to_chat_in_any_situation"]:
            self.connection = DEBUG.debug_connection
            first_msg = self._recv_data()
            self._succeed_login(first_msg)
            return
        self.connection = create_connection("wss://hack.chat/chat-ws")
        d_nick = self.nick
        if self.password != "":
            d_nick = d_nick + "#" + self.password
        self.send_data({
            "cmd": "join",
            "nick": d_nick,
            "channel": self.channel
        })
        first_msg = self._recv_data()
        if first_msg["cmd"] == "onlineSet":  # 成功进入频道
            self._succeed_login(first_msg)
            pass
        elif first_msg["cmd"] == "warn":  # 无法进入
            # 1. 频率限制 [channel=false]
            if not first_msg["channel"]:
                print("rate limit")
                if first_msg["id"] == 21:
                    self.signals_window["signal_qmessagebox_warning"].emit(("Warning",
                                                                            "You are joining channels too fast. "
                                                                            "Wait a moment and try again."))
                elif first_msg["id"] == 22:
                    self.signals_window["signal_qmessagebox_warning"].emit(("Warning",
                                                                            "Nickname must consist of up to 24 letters,"
                                                                            " numbers, and underscores"))
            # 2. 验证码 [channel=self.channel]
            else:
                # start *************验证码转图片********************************************************
                captcha_content = self._recv_data()
                es = 1
                fpa = ".\\res\\temp\\x%d_%d_%s_%s.png" % (es, time.time(), self.channel, self.nick)
                string2png(captcha_content["text"], fpa, eachsize=es)
                # end ***************验证码转图片********************************************************
                # 激活添加验证码部分信号
                self.signals_loginlayout["signal_show_captcha"].emit(fpa)
                try:
                    # 输入验证码后收到的第一条信息
                    first_msg_aft_captcha = self._recv_data()
                    if first_msg_aft_captcha["cmd"] == "onlineSet":
                        self._succeed_login(first_msg_aft_captcha)
                except WebSocketConnectionClosedException as e:
                    # 如果输入了错误的验证码服务器将会断开连接,再接收消息程序会抛出此异常
                    print("wrong captcha", e)
                    self.signals_window["signal_qmessagebox_warning"].emit(("Warning", "You entered the wrong captcha"))
                    self.signals_loginlayout["signal_hide_captcha"].emit()


class LoginLayout(QGridLayout):
    # 创建信号
    signal_show_captcha = pyqtSignal(str)  # str接收验证码图片地址
    signal_hide_captcha = pyqtSignal()  # 隐藏识别码部分

    def __init__(self, signals_window):
        """
        登录页面
        """
        super().__init__()

        # 连接信号与槽
        self.signal_show_captcha.connect(self._show_captcha)
        self.signal_hide_captcha.connect(self._hide_captcha)
        # 包含所有信号
        self.signals_window = signals_window
        self._signals = {
            "signal_show_captcha": self.signal_show_captcha,
            "signal_hide_captcha": self.signal_hide_captcha
        }

        # start ************* 布局设置 *************
        self._default_setting()
        # end *************** 布局设置 *************
        self._setup_ui()

    def _setup_ui(self):
        # start ************* 控件 *************
        # QLabel: 客户端logo
        label_logo = QLabel()
        label_logo.setText("hcclient")
        label_logo.setAlignment(Qt.AlignCenter)
        label_logo.setObjectName("logo")
        label_logo.setProperty("position", "login")
        # QLabel: 名称
        label_nick = QLabel()
        label_nick.setText("NICK")
        # QLineEdit: 名称输入框
        self.lineedit_nick = QLineEdit()
        self.lineedit_nick.setObjectName("login")
        self.lineedit_nick.textChanged.connect(self._check_nick_channel_empty)
        # QLabel: 密码
        label_password = QLabel()
        label_password.setText("PASSWORD")
        # QLineEdit: 密码输入框
        self.lineedit_password = QLineEdit()
        self.lineedit_password.setEchoMode(QLineEdit.Password)  # 密码星星
        self.lineedit_password.setObjectName("login")
        # QLabel: 频道
        label_channel = QLabel()
        label_channel.setText("CHANNEL")
        # QComboBox: 频道输入框
        self.combox_channel = QComboBox()
        self.combox_channel.setObjectName("login")
        self.combox_channel.setEditable(True)
        self.combox_channel.setMaxVisibleItems(6)
        self.combox_channel.setMaxCount(len(common.CHANNELS))
        self.combox_channel.currentTextChanged.connect(self._check_nick_channel_empty)
        for i, item in enumerate(common.CHANNELS):
            if item[0] is None:
                self.combox_channel.addItem(item[1])
            else:
                self.combox_channel.addItem(QIcon(item[0]), item[1])
        # QPushButton: 确认按钮
        self.pushbutton_enter = QPushButton()
        self.pushbutton_enter.setProperty("is_enter_button", True)
        self.pushbutton_enter.setMinimumWidth(120)
        self.pushbutton_enter.setEnabled(False)  # 设置为不可用
        self.pushbutton_enter.setText("->")
        self.pushbutton_enter.clicked.connect(self._login)
        # QLabel: captcha
        label_captcha = QLabel()
        label_captcha.setVisible(False)
        label_captcha.setProperty("captcha", True)
        label_captcha.setText("CAPTCHA")
        # QLabel: 验证码图像
        label_captcha_image = QLabel()
        label_captcha_image.setVisible(False)
        label_captcha_image.setProperty("captcha", True)
        label_captcha_image.setProperty("isimage", True)
        label_captcha_image.setScaledContents(True)  # 可拉伸
        label_captcha_image.setMinimumHeight(40)
        label_captcha_image.setMaximumHeight(70)
        # QLineEdit: 验证码输入框
        self.lineedit_captcha = QLineEdit()
        self.lineedit_captcha.setVisible(False)
        self.lineedit_captcha.setProperty("captcha", True)
        self.lineedit_captcha.setProperty("is_enter_captcha", True)
        self.lineedit_captcha.setMaximumWidth(177)
        self.lineedit_captcha.textChanged.connect(self._check_captcha_empty)
        # QPushButton: 验证码确认按钮
        self.pushbutton_push_captcha = QPushButton()
        self.pushbutton_push_captcha.setVisible(False)
        self.pushbutton_push_captcha.setProperty("captcha", True)
        self.pushbutton_push_captcha.setMinimumWidth(120)
        self.pushbutton_push_captcha.setEnabled(False)
        self.pushbutton_push_captcha.setText("->")
        self.pushbutton_push_captcha.clicked.connect(self._push_captcha_input)
        # end *************** 控件 *************

        # start ************* 添加控件到布局 *************
        # 第一行
        row = 0
        self.addWidget(label_logo, row, 0, 1, 2)
        # 第二行
        row = 1
        self.addWidget(label_nick, row, 0)
        self.addWidget(self.lineedit_nick, row, 1)
        # 第三行
        row = 2
        self.addWidget(label_password, row, 0)
        self.addWidget(self.lineedit_password, row, 1)
        # 第四行
        row = 3
        self.addWidget(label_channel, row, 0)
        self.addWidget(self.combox_channel, row, 1)
        # 第五行
        row = 4
        self.addWidget(self.pushbutton_enter, row, 1, Qt.AlignRight)
        # 第六行
        row = 5
        self.addWidget(label_captcha, row, 0, Qt.AlignTop)
        self.addWidget(label_captcha_image, row, 1)
        # 第七行
        row = 6
        self.addWidget(self.lineedit_captcha, row, 0, 1, 2, Qt.AlignLeft)
        self.addWidget(self.pushbutton_push_captcha, row, 1, Qt.AlignRight)
        # end *************** 添加控件到布局 *************

        # start *************信号*************
        if DEBUG.de["print_if_login_layout_widgets_destroyed"]:
            for i in range(self.count()):
                current_item = self.itemAt(i).widget()
                print("[In LoginLayout] %s.destroyed is connected" % str(current_item))
                current_item.destroyed.connect(lambda: print("[In LoginLayout] A widget is destroyed"))
        # end ***************信号*************

    def _default_setting(self):
        """
        布局默认设置
        :return:
        """
        self.setContentsMargins(275, 150, 275, 150)
        self.setVerticalSpacing(15)  # 行间距

    def _login(self):
        """
        获取nick输入框,password输入框,channel输入框中的值,为Window中登录的函数提供参数
        :return: 成功为True,失败为False
        """
        self._hide_captcha()
        nick = self.lineedit_nick.text()
        password = self.lineedit_password.text()
        channel = self.combox_channel.currentText()
        self.thp = QtHackchatPort(channel, nick, password, self.signals_window, self._signals)
        self.thp.start()
        return True

    def _push_captcha_input(self):
        """
        将输入的验证码传给服务端
        :return:
        """
        if self.lineedit_captcha is not None and self.thp is not None:
            self.thp.send_data({
                "cmd": "chat",
                "text": str(self.lineedit_captcha.text())
            })

    def _check_nick_channel_empty(self):
        """
        检查nick输入框或channel输入框是否为空
        如果nick或channel输入框为空,将按钮设置为不可用
        反之设置为可用
        :return:
        """
        nick = self.lineedit_nick.text()
        channel = self.combox_channel.currentText()
        if nick.strip() != "" and channel.strip() != "":
            self.pushbutton_enter.setEnabled(True)
        else:
            self.pushbutton_enter.setEnabled(False)

    def _check_captcha_empty(self):
        """
        检查验证码输入框是否为空
        如果验证码输入框为空,将按钮设置为不可用
        反之设置为可用
        :return:
        """
        captcha = self.lineedit_captcha.text()
        if captcha.strip() != "":
            self.pushbutton_push_captcha.setEnabled(True)
        else:
            self.pushbutton_push_captcha.setEnabled(False)

    def _show_captcha(self, filepath):
        """
        显示验证码部分
        :param filepath: 验证码图片地址
        :return:
        """
        self.setContentsMargins(275, 75, 275, 100)
        # 将所有captcha部件设为可见
        for i in reversed(range(self.count())):
            w = self.itemAt(i).widget()
            if w.property("is_enter_button"):
                w.setText("Re-Enter")
            if w.property("isimage"):
                w.setPixmap(QPixmap(filepath))
            if w.property("captcha"):
                w.show()

    def _hide_captcha(self):
        self.setContentsMargins(275, 150, 275, 150)  # 出现识别码后的布局
        # 将所有captcha部件设为隐藏
        for i in reversed(range(self.count())):
            w = self.itemAt(i).widget()
            # 将按钮文本设置为默认
            if w.property("is_enter_button"):
                w.setText("->")
            # 清空验证码输入框文本
            if w.property("is_enter_captcha"):
                w.setText("")
            if w.property("captcha"):
                w.hide()


class QtDataHandler(QThread):
    @staticmethod
    def render_message(message):
        """
        将消息根据类别渲染成html
        :param message: 数据
        :return: None不显示
        """
        final_text = ""
        cmd = message["cmd"]
        if cmd == "onlineSet":
            nicks = message["nicks"]
            # users = message["users"]]
            final_text += Label.font("%s Users online: %s" % (Label.b("*"), ", ".join(nicks)), color="#2e541a")

        elif cmd == "chat":  # 聊天消息
            nick = message["nick"]
            text = message["text"].replace("\n", "<br>")
            trip = message.get("trip")
            color = message.get("color")
            if trip is not None:
                final_text += Label.font(trip, color="#6e6b5e")
                final_text += " "
            trip_nick = nick
            if color is not None:
                trip_nick = font(nick, color=color)
            final_text += Label.b(trip_nick)
            final_text += Label.br + text

        elif cmd == "onlineAdd":
            nick = message["nick"]
            trip = message.get("trip")
            final_text += Label.font("%s %s joined" % (Label.b("*"), nick), color="#2e541a")

        elif cmd == "onlineRemove":
            nick = message["nick"]
            trip = message.get("trip")
            final_text += Label.font("%s %s left" % (Label.b("*"), nick), color="#2e541a")

        elif cmd == "warn":
            text = message["text"].replace("\n", "<br>")
            final_text += Label.font("%s %s" % (Label.b("!"), text), color="#cfb017")

        elif cmd == "info":
            tp = message.get("type")
            if tp is None:
                text = message["text"].replace("\n", "<br>")
                final_text += Label.font("%s %s" % (Label.b("*"), text), color="#2e541a")
            elif tp == "whisper":
                text = message["text"].replace("\n", "<br>")
                from_ = message["from"]
                final_text += Label.b(Label.font("(whisper)", color="#2e541a"))
                final_text += " "
                if type(from_) == str:  # 别人发的
                    trip = message.get("trip")
                    if trip is not None:  # 有识别码
                        final_text += Label.font(trip, color="#6e6b5e")
                else:  # 自己发的
                    pass
                final_text += Label.br
                final_text += text
            else:
                return None

        else:
            return None

        return final_text + Label.br

    def __init__(self, signals_window, signals_chatlayout, connection, first_msg):
        """
        处理来自服务器发送的信息
        :param signals_window: window的所有信号
        :param signals_chatlayout: chatlayout的所有信号
        :param connection: WebSocket连接
        :param first_msg: 收到的第一条消息(onlineSet)
        """
        super().__init__()

        self.signals_window = signals_window
        self.signals_chatlayout = signals_chatlayout
        self.connection = connection
        self.first_msg = first_msg

    def _recv_data(self):
        """
        返回收到的消息
        :return: json转化的dict
        """
        data = self.connection.recv()
        if data is not None:
            data = json.loads(data)
        else:
            return None
        if DEBUG.de["print_all_received_data"]:
            print(data)
        return data

    def run(self):
        self.signals_chatlayout["signal_add_text_to_chat"].emit(QtDataHandler.render_message(self.first_msg))

        while True:
            try:
                message = self._recv_data()
                if message is None:
                    continue
                rm = QtDataHandler.render_message(message)
                if rm is None:
                    continue
                self.signals_chatlayout["signal_add_text_to_chat"].emit(rm)
            except Exception as e:
                print("[Error In QtDataHandler]", e)


class SendTextEdit(QTextEdit):
    def __init__(self, signals_window, signals_chatlayout):
        super().__init__()
        self.signals_window = signals_window
        self.signals_chatlayout = signals_chatlayout

    def keyPressEvent(self, evt):
        """
        按下键盘事件
        :param evt:
        :return:
        """
        if evt.modifiers() == Qt.ShiftModifier and evt.key() == Qt.Key_Return:
            pass
            # self.signals_chatlayout["signal_add_text_to_send"].emit("\n")
            # super().keyPressEvent(evt)
        elif evt.key() == Qt.Key_Return:
            # shift + enter 换行
            self.signals_chatlayout["signal_send_message"].emit()
            super().keyPressEvent(evt)
            self.setText("")
            return None
        super().keyPressEvent(evt)
        return None


class ChatLayout(QGridLayout):
    signal_add_text_to_chat = pyqtSignal(str)  # 在文本框后追加文本
    signal_send_message = pyqtSignal()
    signal_add_text_to_send = pyqtSignal(str)  # 向输入框中添加文本

    def __init__(self, signals_window, connection, first_msg):
        """
        聊天页面
        """
        super().__init__()
        self.signals_window = signals_window
        self.connection = connection

        # 连接信号与槽
        self.signal_add_text_to_chat.connect(self.add_text_to_chat)
        self.signal_send_message.connect(self.send_message)
        self.signal_add_text_to_send.connect(self.add_text_to_send)
        # 包含所有信号
        self._signals = {
            "signal_add_text_to_chat": self.signal_add_text_to_chat,
            "signal_send_message": self.signal_send_message,
            "signal_add_text_to_send": self.signal_add_text_to_send
        }

        self._setup_ui()

        # 启动数据处理器(处理从客户端收来的信息)
        self.qdh = QtDataHandler(self.signals_window, self._signals, self.connection, first_msg)
        self.qdh.start()

    def add_text_to_send(self, text):
        """
        向输入框中添加文本
        :param text: 要添加的文本
        :return:
        """
        self.textedit_send_message.append(text)

    def send_message(self):
        """
        获取输入框中的文本并发送
        :return:
        """
        text = self.textedit_send_message.toPlainText().strip()
        if text == "":  # 禁止发送空白消息
            return
        self.connection.send(json.dumps({
            "cmd": "chat",
            "text": text
        }))

    def add_text_to_chat(self, text):
        """
        添加文本到展示框(展示聊天消息)中
        :param text: 文本
        :return:
        """
        self.textedit_chat_message.append(text)

    def _setup_ui(self):
        # start ************* 控件 *************
        # QTextEdit: 聊天消息
        self.textedit_chat_message = QTextEdit()
        self.textedit_chat_message.setObjectName("chat")
        self.textedit_chat_message.setProperty("tp", "show")
        # QTextEdit: 聊天输入框
        self.textedit_send_message = SendTextEdit(self.signals_window, self._signals)
        self.textedit_send_message.setMaximumHeight(75)
        self.textedit_send_message.setObjectName("chat")
        self.textedit_send_message.setProperty("tp", "send")
        # end *************** 控件 *************

        # start ************* 添加控件到布局 *************
        self.addWidget(self.textedit_chat_message, 0, 0)
        self.addWidget(self.textedit_send_message, 1, 0)
        # end *************** 添加控件到布局 *************


class Window(QWidget):
    WIDTH = 856
    HEIGHT = 575
    SIZE = (WIDTH, HEIGHT)

    # 创建信号
    signal_qmessagebox_warning = pyqtSignal(tuple)  # 弹出警告弹窗
    signal_turn_to_layout_login = pyqtSignal()  # 转到登录页面
    signal_turn_to_layout_chat = pyqtSignal(tuple)  # 转到聊天页面, tuple -> (connection: WebSocket, first_msg: dict)

    def __init__(self):
        QWidget.__init__(self)

        # 连接信号与槽
        self.signal_qmessagebox_warning.connect(self.warning)
        self.signal_turn_to_layout_login.connect(self.turn_to_loginlayout)
        self.signal_turn_to_layout_chat.connect(self.turn_to_chatlayout)
        # 包含所有信号(通常需要用到QWidget(顶级窗口))
        self._signals = {
            "signal_qmessagebox_warning": self.signal_qmessagebox_warning,
            "signal_turn_to_layout_login": self.signal_turn_to_layout_login,
            "signal_turn_to_layout_chat": self.signal_turn_to_layout_chat
        }

        self.setWindowTitle("hcclient(test)")
        self.resize(*self.SIZE)
        self.setup_ui()
        # 窗口大小显示 (测试用)
        self.label_window_size = QLabel(self)
        self.label_window_size.resize(250, 30)
        if not DEBUG.de["show_window_size"]:
            self.label_window_size.hide()
        self.move_to_centre()

    def warning(self, a):
        """
        警告弹窗
        :param a: (弹窗标题,弹窗内容)
        :return:
        """
        QMessageBox.warning(self, a[0], a[1], QMessageBox.Close)

    def resizeEvent(self, evt):
        """
        测试用,显示窗口大小
        :param evt:
        :return:
        """
        text = "win size: %d,%d" % (self.size().width(), self.size().height())
        self.label_window_size.setText(text)

    def turn_to_loginlayout(self):
        """
        转到登陆页面
        :return:
        """
        login_layout = LoginLayout(self._signals)
        if DEBUG.de["print_if_login_layout_widgets_destroyed"]:
            login_layout.destroyed.connect(lambda: print("loginlayout is destroyed, "
                                                         "the current layout is %s" % self.layout()))
        self.setLayout(login_layout)

    def turn_to_chatlayout(self, cf):
        """
        转到聊天页面
        :param cf: connection, first_msg
        connection: 登录时创建好的WebSocket连接
        first_msg: 收到的第一条信息
        :return:
        """
        connection, first_msg = cf
        current_layout = self.layout()
        for i in reversed(range(current_layout.count())):
            current_layout.itemAt(i).widget().deleteLater()
        # * #  * #  * #  * #  * #  * #  * #  * #  * #  * #  * #
        chat_layout = ChatLayout(self._signals, connection, first_msg)

        # 设置chatlayout为新布局(将setLayout绑定到destroyed的信号上,delete_later不会立刻将布局删除)
        def temp():
            # self.resize(Window.WIDTH + 100, Window.HEIGHT + 100)
            self.setLayout(chat_layout)
            # self.move_to_centre()

        current_layout.destroyed.connect(temp)
        current_layout.deleteLater()

    def move_to_centre(self):
        """
        将窗口移动到屏幕中间
        :return:
        """
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def setup_ui(self):
        with open("style.qss", "r") as f:
            qApp.setStyleSheet(f.read())  # 全局样式
        qApp.setFont(QFont("Courier New"))  # 所有字体设为Courier New
        self._signals["signal_turn_to_layout_login"].emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
