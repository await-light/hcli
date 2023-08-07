from PIL import Image, ImageDraw

COL_WHITE = (255, 255, 255)
COL_BLACK = (0, 0, 0)


def string2png(string,
               save_path_with_filename,
               eachsize: int = 2,
               fontcolor: tuple = COL_WHITE,
               backgroundcolor: tuple = COL_BLACK):
    """
    将hackchat验证码转化为png图片
    :param string: 文本
    :param save_path_with_filename: 相对路径及文件名
    :param eachsize: 一个#的边长,单位:像素
    :param fontcolor: 字体颜色(RGB元组)
    :param backgroundcolor: 背景颜色(RGB元组)
    :return: (长,宽)
    """
    new = [[]]
    row = 0
    for i in string:
        if i == " ":
            new[row].append(0)
        elif i == "#":
            new[row].append(1)
        elif i == "\n":
            row += 1
            new.append([])
    eachb = eachsize
    width = len(new[0]) * eachb
    height = len(new) * eachb
    image = Image.new('RGB', (width, height), backgroundcolor)
    for ir, r in enumerate(new):
        for ic, c in enumerate(r):
            if c == 1:
                image.paste(fontcolor, (ic * eachb, ir * eachb, (ic + 1) * eachb, (ir + 1) * eachb))
    image.save(save_path_with_filename)
    return width, height
