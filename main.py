import os
import cv2
import time
import shutil
import codecs
import threading
import numpy as np
import Play_mp3
from PIL import ImageGrab
from paddleocr import PaddleOCR


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super().__init__()
        self.func = func
        self.args = args
        self.result = None

    def run(self):
        self.result = self.func(*self.args)

    def get_args(self):
        return self.args

    def get_result(self):
        return self.result


def log(msg, debug=True):
    if debug:
        print(msg)


def crab_stream():
    im = ImageGrab.grab()
    im.save('crab.png')


def ocr(img, lang='ch'):
    reader = PaddleOCR(lang=lang)
    result = reader.ocr(img)
    return result


def author_id(ocr_result):
    author = {'text': '', 'reliability': 0}
    map_id = {'text': '', 'reliability': 0}
    map_title = {'text': '', 'reliability': 0}
    for line in ocr_result:
        loc = line[0][0]
        text = line[1][0]
        reliability = line[1][1]
        if 130 < loc[1] < 200:
            map_title['text'] = text
            map_title['reliability'] = reliability
        elif 250 < loc[1] < 310:
            if 110 < loc[0] < 360:
                map_id['text'] = text
                map_id['reliability'] = reliability
            else:
                author['text'] = text
                author['reliability'] = reliability
    return {'author': author, 'map_id': map_id, 'map_title': map_title}


def map_info(img):
    en = author_id(ocr(img, lang='en'))
    jp = author_id(ocr(img, lang='japan'))
    author = sorted([en, jp], key=lambda x: x['author']['reliability'], reverse=True)[0]['author']['text']
    map_id = sorted([en, jp], key=lambda x: x['map_id']['reliability'], reverse=True)[0]['map_id']['text']
    map_title = sorted([en, jp], key=lambda x: x['map_title']['reliability'], reverse=True)[0]['map_title']['text']
    if author == '' or map_id == '' or map_title == '':
        log('获取信息不完整')
        shutil.copy('crab.png', 'motion/map{0}.png'.format(time.time()))
        return
    f = codecs.open('C:/Users/tentem/Code/Python/mariomaker/map/author.txt', 'w', 'utf-8')
    f.write(author)
    f.close()
    f = codecs.open('C:/Users/tentem/Code/Python/mariomaker/map/id.txt', 'w', 'utf-8')
    f.write(map_id)
    f.close()
    f = codecs.open('C:/Users/tentem/Code/Python/mariomaker/map/title.txt', 'w', 'utf-8')
    f.write(map_title)
    f.close()


def template_match(src, temp, threshold):
    is_match = False
    im_rgb = cv2.imread(src)
    im_gray = cv2.cvtColor(im_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread('template/' + temp, 0)
    res = cv2.matchTemplate(im_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    for pt in zip(*loc[::-1]):
        is_match = True
    return is_match


def templates_match(src, templates, threshold):
    threads = []
    for template in templates:
        threads.append(MyThread(template_match, (src, template, threshold)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for thread in threads:
        result = thread.get_result()
        if result:
            return thread.get_args()[1]


def get_role():
    role_img = templates_match('crab.png', ['mario.png', 'luigi.png', 'kinopio.png', 'kinopiko.png'], 0.99)
    if role_img:
        role = role_img.split('.')[0]
        return role
    else:
        shutil.copy('crab.png', 'motion/role{0}.png'.format(time.time()))


def change_role(role):
    if not role:
        return
    else:
        shutil.copy('role/' + role + '.png', 'C:/Users/tentem/Pictures/current_role.png')


def play_audio():
    is_find = 0
    templates = []
    for i in range(1, 22):
        templates.append('message{0}.png'.format(i))
    matched = templates_match('crab.png', templates, 0.9)
    if matched:
        index = matched.split('message')[1].split('.')[0]
        is_find = index
    if is_find == 0:
        shutil.copy('crab.png', 'motion/message{0}.png'.format(time.time()))
    else:
        music = 'audio/{0}.mp3'.format(index)
        Play_mp3.play(music)
        time.sleep(0.1)
    return is_find


if __name__ == '__main__':
    find_dialog = False
    find_player = None
    while True:
        crab_stream()
        if template_match('crab.png', 'matched.png', 0.9):
            log('检测到匹配到选手')
            if find_player:
                log('已完成匹配')
            else:
                log('尚未匹配')
            if not find_player:
                role = get_role()
                log('匹配到的角色为：{0}'.format(role))
                change_role(role)
                find_player = role
        elif template_match('crab.png', 'begin_game.png', 0.9):
            log('检测到开始游戏')
            map_info('crab.png')
        elif template_match('crab.png', 'dialog.png', 0.9):
            log('检测到对话框')
            if find_dialog:
                log('已完成匹配')
            else:
                log('尚未匹配')
            if not find_dialog:
                audio = play_audio()
                log('找到的歌曲序列为：{0}'.format(audio))
                find_dialog = True
        else:
            find_dialog = False
            find_player = None
