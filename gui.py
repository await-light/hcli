import sys
import json
import time
import queue

from PyQt5.Qt import *
import websocket._exceptions
from websocket import create_connection

import hccommon
from captcha import string2png


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
        self.connection = create_connection("wss://hack.chat/chat-ws")
        d_nick = self.nick
        if self.password != "":
            d_nick = d_nick + "#" + self.password
        self.send_data({
            "cmd": "join",
            "nick": d_nick,
            "channel": self.channel
        })
        first_msg = json.loads(self.connection.recv())
        print(first_msg)
        if first_msg["cmd"] == "onlineSet":  # 成功进入频道
            # for i in reversed(range(self.login_layout.count())):
            # self.login_layout.itemAt(i).widget().setParent(None)
            print("enter the channel successfully")
            pass
        elif first_msg["cmd"] == "warn":  # 无法进入
            # 1. 频率限制 [channel=false]
            if not first_msg["channel"]:
                print("rate limit")
                self.signals_window["signal_qmessagebox_warning"].emit(("Warning",
                                                                        "You are joining channels too fast. "
                                                                        "Wait a moment and try again."))
            # 2. 验证码 [channel=self.channel]
            else:
                print("captcha")
                # start *************验证码转图片********************************************************
                captcha_content = json.loads(self.connection.recv())
                _es = 1
                fpa = ".\\res\\temp\\x%d_%d_%s_%s.png" % (_es, time.time(), self.channel, self.nick)
                string2png(captcha_content["text"], fpa, eachsize=_es)
                # end ***************验证码转图片********************************************************
                # 激活添加验证码部分信号
                self.signals_loginlayout["signal_show_captcha"].emit(fpa)
                try:
                    # 输入验证码后收到的第一条信息
                    msgaftcap = json.loads(self.connection.recv())
                    if msgaftcap["cmd"] == "onlineSet":
                        print("enter the channel successfully")
                except Exception as e:
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
        self.combox_channel.setMaxCount(len(hccommon.CHANNELS))
        self.combox_channel.currentTextChanged.connect(self._check_nick_channel_empty)
        for i, item in enumerate(hccommon.CHANNELS):
            if item[0] is None:
                self.combox_channel.addItem(item[1])
            else:
                self.combox_channel.addItem(QIcon(item[0]), item[1])
        # QPushButton: 确认按钮
        self.pushbutton_enter = QPushButton()
        self.pushbutton_enter.setProperty("isenterbutton", True)
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
        self.lineedit_captcha.setProperty("isentercaptcha", True)
        self.lineedit_captcha.setMaximumWidth(177)
        self.lineedit_captcha.textChanged.connect(self._check_captcha_empty)
        # QPushButton: 验证码确认按钮
        self.pushbutton_pushcaptcha = QPushButton()
        self.pushbutton_pushcaptcha.setVisible(False)
        self.pushbutton_pushcaptcha.setProperty("captcha", True)
        self.pushbutton_pushcaptcha.setMinimumWidth(120)
        self.pushbutton_pushcaptcha.setEnabled(False)
        self.pushbutton_pushcaptcha.setText("->")
        self.pushbutton_pushcaptcha.clicked.connect(self._push_captcha_input)
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
        self.addWidget(self.pushbutton_pushcaptcha, row, 1, Qt.AlignRight)
        # end *************** 添加控件到布局 *************

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
            self.pushbutton_pushcaptcha.setEnabled(True)
        else:
            self.pushbutton_pushcaptcha.setEnabled(False)

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
            if w.property("isenterbutton"):
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
            if w.property("isenterbutton"):
                w.setText("->")
            # 清空验证码输入框文本
            if w.property("isentercaptcha"):
                w.setText("")
            if w.property("captcha"):
                w.hide()

class ChatLayout(QGridLayout):
    def __init__(self, signals_window):
        """
        聊天页面
        """
        super().__init__()
        self.signals_window = signals_window

    def setup_ui(self):
        pass


class Window(QWidget):
    WIDTH = 856
    HEIGHT = 575
    SIZE = (WIDTH, HEIGHT)

    # 创建信号
    signal_qmessagebox_warning = pyqtSignal(tuple)  # 弹出警告弹窗
    signal_turn_to_layout_login = pyqtSignal()  # 转到登录页面
    signal_turn_to_layout_chat = pyqtSignal()  # 转到聊天页面

    def __init__(self):
        QWidget.__init__(self)

        # 连接信号与槽
        self.signal_qmessagebox_warning.connect(self.warning)
        self.signal_turn_to_layout_login.connect(self.turn_to_loginlayout)
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

    def warning(self, a):
        """
        警告弹窗
        :param a: (弹窗标题,弹窗内容)
        :return:
        """
        QMessageBox.warning(self,
                            a[0],
                            a[1],
                            QMessageBox.Close)

    def resizeEvent(self, evt):
        """
        测试用,显示窗口大小
        :param evt:
        :return:
        """
        text = "win size: %d,%d" % (self.size().width(), self.size().height())
        self.label_window_size.setText(text)

    def turn_to_loginlayout(self):
        login_layout = LoginLayout(self._signals)
        self.setLayout(login_layout)

    def turn_to_chatlayout(self):
        chat_layout = ChatLayout(self._signals)
        self.setLayout(chat_layout)

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