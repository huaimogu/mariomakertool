import cv2
import shutil
import device
import codecs
import threading
import numpy as np
from tkinter import *
from tkinter.ttk import Combobox
from playsound import playsound
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


def ocr(img, lang='ch'):
    reader = PaddleOCR(lang=lang, use_gpu=False, show_log=False, use_angle_cls=True)
    result = reader.ocr(img)
    text = ''
    reliability = 0
    for word in result[0]:
        text += word[1][0] + ' '
        reliability += word[1][1]
    text = text.strip()
    reliability = reliability / len(result[0])
    return text, reliability


def ocr_multilang(img, langs):
    max_reliability = 0
    for lang in langs:
        text, reliability = ocr(img, lang)
        if reliability > max_reliability:
            result = text
            max_reliability = reliability
    return result


def map_info(zoom_rate, img):
    author_image = img[int(250 * zoom_rate):int(320 * zoom_rate), int(1300 * zoom_rate):int(1800 * zoom_rate)]
    id_image = img[int(250 * zoom_rate):int(320 * zoom_rate), int(110 * zoom_rate):int(440 * zoom_rate)]
    title_image = img[int(130 * zoom_rate):int(200 * zoom_rate), int(120 * zoom_rate):int(1800 * zoom_rate)]
    author = ocr_multilang(author_image, ['en'])
    map_id = ocr_multilang(id_image, ['ch', 'japan'])
    map_title = ocr_multilang(title_image, ['ch', 'japan'])
    if map_id != '':
        f = codecs.open('map/author.txt', 'w', 'utf-8')
        f.write(author)
        f.close()
        f = codecs.open('map/id.txt', 'w', 'utf-8')
        f.write(map_id)
        f.close()
        f = codecs.open('map/title.txt', 'w', 'utf-8')
        f.write(map_title)
        f.close()
        return True
    else:
        return False


def template_match(zoom_rate, src, temp, threshold):
    is_match = False
    src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    src = cv2.resize(src, (0, 0), fx=zoom_rate, fy=zoom_rate)
    template = cv2.imread('template/' + temp, 0)
    res = cv2.matchTemplate(src, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    for pt in zip(*loc[::-1]):
        is_match = True
    return is_match


def templates_match(zoom_rate, src, templates, threshold):
    threads = []
    for template in templates:
        threads.append(MyThread(template_match, (zoom_rate, src, template, threshold)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for thread in threads:
        result = thread.get_result()
        if result:
            return thread.get_args()[2]


def get_role(zoom_rate, frame):
    role_img = templates_match(zoom_rate, frame, ['mario.png', 'luigi.png', 'kinopio.png', 'kinopiko.png'], 0.9)
    if role_img:
        role = role_img.split('.')[0]
        return role
    else:
        return None


def change_role(role):
    if not role:
        return
    else:
        shutil.copy('role/' + role + '.png', 'role/current_role.png')


def play_audio(zoom_rate, frame):
    is_find = 0
    templates = []
    for i in range(1, 22):
        templates.append('message{0}.png'.format(i))
    matched = templates_match(zoom_rate, frame, templates, 0.8)
    if matched:
        index = matched.split('message')[1].split('.')[0]
        is_find = index
    if is_find != 0:
        music = 'audio/{0}.mp3'.format(index)
        playsound(music)
    return is_find


def device_changed(event):
    comboxResolution.config(values=camera_devices[comboxDevice.get()][1])
    comboxResolution.current(0)


def monitor():
    frame_width = int(comboxResolution.get().split('x')[0])
    frame_height = int(comboxResolution.get().split('x')[1])
    zoom_rate = 1920 / frame_width
    capture = cv2.VideoCapture(camera_devices[comboxDevice.get()][0])
    capture.set(3, frame_width)
    capture.set(4, frame_height)
    find_dialog = 0
    find_player = None
    find_map = False
    while is_monitoring:
        ret, frame = capture.read()
        if template_match(zoom_rate, frame[int(876 / zoom_rate):int(1056 / zoom_rate), 1:frame_width], 'player.png', 0.9):
            if find_player is None:
                find_player = get_role(zoom_rate, frame[int(834 / zoom_rate):int(900 / zoom_rate), 1:frame_width])
                change_role(find_player)
        elif template_match(zoom_rate, frame[int(348 / zoom_rate):int(474 / zoom_rate), int(1602 / zoom_rate):int(1800 / zoom_rate)], 'start.png', 0.9):
            if not find_map:
                find_map = map_info(zoom_rate, frame)
        elif template_match(zoom_rate, frame[int(936 / zoom_rate):int(1020 / zoom_rate), int(180 / zoom_rate):int(402 / zoom_rate)], 'dialog.png', 0.8):
            if find_dialog == 0:
                find_dialog = play_audio(zoom_rate, frame[int(936 / zoom_rate):int(1020 / zoom_rate), int(180 / zoom_rate):int(402 / zoom_rate)])
        else:
            find_dialog = 0
            find_player = None
            find_map = False
        cv2.waitKey(250)
    capture.release()
    cv2.destroyAllWindows()


def button_click():
    global is_monitoring
    is_monitoring = not is_monitoring
    if is_monitoring:
        buttonMonitor.config(text='停止监听')
        t = MyThread(monitor)
        t.start()
    else:
        buttonMonitor.config(text='开始监听')


if __name__ == '__main__':
    camera_index = 0
    camera_devices = {}
    camera_list = device.getDeviceList()
    for camera in camera_list:
        camera_devices[camera[0]] = [camera_index, ['{0}x{1}'.format(k[0], k[1]) for k in set(camera[1])]]
        camera_index = camera_index + 1
    window = Tk()
    window.title('mario maker2 tool')
    window.geometry('500x250')
    Label(window, text='设备').place(x=150, y=50)
    Label(window, text='分辨率').place(x=150, y=100)
    comboxDevice = Combobox(window, values=list(camera_devices.keys()))
    comboxDevice.place(x=200, y=50)
    comboxResolution = Combobox(window, values=camera_devices[list(camera_devices.keys())[0]][1])
    comboxResolution.place(x=200, y=100)
    comboxDevice.current(0)
    comboxResolution.current(0)
    comboxDevice.bind('<<ComboboxSelected>>', device_changed)
    is_monitoring = False
    buttonMonitor = Button(window, text='开始监听', command=button_click, width=29)
    buttonMonitor.place(x=150, y=150)
    window.mainloop()