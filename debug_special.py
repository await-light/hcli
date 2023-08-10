import json


class DebugWebSocket:
    def __init__(self, received_message_list):
        """
        加入hack.chat次数过多会触发频率限制机制
        此类目的为在调试时替代真实连接以防被限制
        """
        self.received_message_list = [json.dumps(i) for i in received_message_list]

    def recv(self):
        if len(self.received_message_list) > 0:
            msg = self.received_message_list[0]
            del self.received_message_list[0]
            return msg
        else:
            return None

    def send(self, data):
        text = json.loads(data)["text"]
        # TODO 补全模拟服务端发来的chat消息参数
        self.received_message_list.append(json.dumps({
            "cmd": "chat",
            "nick": "none",
            "text": text
        }))
