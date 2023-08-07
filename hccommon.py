import random


def _random_channel():
    return "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for i in range(8)])


CHANNELS = [
    (None, ""),
    ("./res/hackchaticon.png", "your-channel"),
    ("./res/hackchaticon.png", "lounge"),
    ("./res/hackchaticon.png", "meta"),
    ("./res/hackchaticon.png", "math"),
    ("./res/hackchaticon.png", "physics"),
    ("./res/hackchaticon.png", "chemistry"),
    ("./res/hackchaticon.png", "technology"),
    ("./res/hackchaticon.png", "programming"),
    ("./res/hackchaticon.png", "games"),
    ("./res/hackchaticon.png", "banana")
]

