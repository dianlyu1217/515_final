import tkinter as tk
import RPi.GPIO as GPIO
import threading
import time
from mfrc522 import SimpleMFRC522
import speech_recognition as sr
import db
from typing import List
import my_openai

# 设置GPIO引脚
TOUCH_SENSOR_PIN = 13
# 初始化NFC读卡器
reader = SimpleMFRC522()
# 标记NFC卡的状态
nfc_activated = False
hello_displayed = False
# 语音相关全局参数
origin_sentences: List[str] = []
interviewer1 = 'interviewer1'
interviewer2 = 'interviewer2'
total_duration = 0
cur_role = interviewer1
interview_id = 0


def change_role():
    global cur_role
    if cur_role == interviewer1:
        cur_role = interviewer2
    else:
        cur_role = interviewer1


def setup_gpio():
    GPIO.setwarnings(False)
    if GPIO.getmode() is None or GPIO.getmode() != GPIO.BCM:
        GPIO.cleanup()  # 清理现有的GPIO设置
        GPIO.setmode(GPIO.BCM)
    GPIO.setup(TOUCH_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def monitor_touch_sensor(callback):
    while True:
        if GPIO.input(TOUCH_SENSOR_PIN) == GPIO.HIGH:
            print("Touch detected")
            callback(True)
        time.sleep(0.1)


def place_window(root, width, height):
    x = 0  # 屏幕左侧对齐
    y = 0  # 顶部对齐
    root.geometry(f'{width}x{height}+{x}+{y}')


def on_touch_detected(is_touched):
    global hello_displayed
    if is_touched and nfc_activated and not hello_displayed:
        hello_displayed = True
        hello_label.place(x=0, y=0, width=width, height=height)  # 覆盖整个屏幕
        speech_label.place_forget()
        listening_label.place_forget()
        root.after(3000, hide_hello_label)


def hide_hello_label():
    global hello_displayed
    hello_label.place_forget()
    speech_label.place(x=20, y=100, width=width - 40, height=height - 140)  # 恢复显示
    hello_displayed = False


def update_timer():
    global start_time, nfc_activated
    if nfc_activated:
        elapsed_time = int(time.time() - start_time)
        hours = elapsed_time // 3600
        minutes = (elapsed_time % 3600) // 60
        seconds = elapsed_time % 60
        timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
        timer_label.after(1000, update_timer)


def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        global interview_id
        interview_id = db.insert_interview(0, '', 0)
        while nfc_activated:
            listening_label.place(x=width - 220, y=20)  # Listening 状态标签位置
            try:
                # get audio
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                duration = int(len(audio.frame_data) / (audio.sample_rate * audio.sample_width))
                # get origin sentence
                origin_sentence = recognizer.recognize_google(audio, language="en-US")
                # get ai sentence
                ai_sentence, label = my_openai.get_sentence_resp(origin_sentence)
                # insert db
                sentence = db.SentenceData(interview_id=interview_id, role=cur_role, origin_sentence=origin_sentence, ai_sentence=ai_sentence, label=label, duration=duration)
                db.insert_sentence(sentence)
                # change variable
                origin_sentences.append(origin_sentence)
                global total_duration
                total_duration = total_duration + duration
                display_speech_text(cur_role + ': ' + origin_sentence)
                change_role()
            except sr.UnknownValueError:
                print("Unable to recognize audio")
            except sr.RequestError as e:
                print(f"Request error: {e}")
            except sr.WaitTimeoutError:
                print("Listening timeout")


def display_speech_text(text: str) -> None:
    if not hello_displayed:
        speech_label.config(state=tk.NORMAL)
        speech_label.insert(tk.END, text + "\n")
        speech_label.config(state=tk.DISABLED)
        speech_label.see(tk.END)  # 自动滚动到底部


def start_nfc_reader():
    global nfc_activated, start_time, elapsed_time
    while True:
        print("Waiting to place your card")
        nfc_label.config(text="Waiting to place your card")

        id, text = reader.read()
        print(f"Card UID: {id}")
        print(f"Card Text: {text}")

        if not nfc_activated:
            nfc_activated = True
            start_time = time.time()
            nfc_label.place_forget()
            timer_label.place(x=20, y=20)
            update_timer()

            speech_label.place(x=20, y=100, width=width - 40, height=height - 140)
            listening_label.place(x=width - 220, y=20)  # Listening 状态标签位置

            speech_thread = threading.Thread(target=recognize_speech)
            speech_thread.daemon = True
            speech_thread.start()

        else:
            nfc_activated = False
            elapsed_time = int(time.time() - start_time)
            hours = elapsed_time // 3600
            minutes = (elapsed_time % 3600) // 60
            seconds = elapsed_time % 60
            total_time = f"Finish time: {hours:02}:{minutes:02}:{seconds:02}"
            # get interview summary
            summary = my_openai.get_interview_resp(origin_sentences)
            db.update_interview(interview_id, summary, total_duration)
            clear_screen()
            nfc_label.config(text=total_time, font=("Helvetica", 40))
            nfc_label.place(relx=0.5, rely=0.5, anchor='center')
            break

        time.sleep(1)


def clear_screen():
    timer_label.place_forget()
    hello_label.place_forget()
    speech_label.place_forget()
    listening_label.place_forget()


setup_gpio()

root = tk.Tk()
root.title("NFC Controlled Timer and Touch Sensor")
root.configure(bg="black")

width = 1280  # 显示器的宽度
height = 720  # 显示器的高度
place_window(root, width, height)

hello_label = tk.Label(root, text=my_openai.get_summary(origin_sentences), font=("Helvetica", 40), anchor='w', bg="black", fg="white", wraplength=300)
hello_label.place_forget()

timer_label = tk.Label(root, text="00:00:00", font=("Helvetica", 40), bg="black", fg="white")

nfc_label = tk.Label(root, text="Waiting to place your card", font=("Helvetica", 40), bg="black", fg="white")
nfc_label.place(relx=0.5, rely=0.5, anchor='center')

speech_label = tk.Text(root, font=("Helvetica", 40), wrap='word', bg="black", fg="white")
speech_label.config(state=tk.DISABLED)
speech_label.place_forget()

listening_label = tk.Label(root, text="Listening...", font=("Helvetica", 40), bg="black", fg="yellow")
listening_label.place_forget()

nfc_thread = threading.Thread(target=start_nfc_reader)
nfc_thread.daemon = True
nfc_thread.start()

touch_thread = threading.Thread(target=monitor_touch_sensor, args=(on_touch_detected,))
touch_thread.daemon = True
touch_thread.start()

root.mainloop()

GPIO.cleanup()
