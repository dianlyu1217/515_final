import time
import my_openai
import db
import os
from typing import List
import csv

# 全局参数
origin_sentences: List[str] = []
manager = 'interviewer1'
candidate = 'interviewer2'
total_duration = 0
cur_role = manager
listening = True


def change_role():
    global cur_role
    if cur_role == manager:
        cur_role = candidate
    else:
        cur_role = manager


def listen_and_respond(origin_sentence: str):
    global listening
    global total_duration
    global origin_sentences
    print("[%s] said: %s" % (cur_role, origin_sentence))
    # 判断终止
    if "stop listening" in origin_sentence.lower():
        print("Stopping listening.")
        listening = False
        return
    # 生成：音频时长，译文，标签
    sentence_duration = 5
    total_duration = total_duration + sentence_duration
    origin_sentences.append(origin_sentence)
    ai_sentence, label = my_openai.get_sentence_resp(origin_sentences)
    # 插入sentence
    sentence = db.SentenceData(
        interview_id=interview_id,
        role=cur_role,
        origin_sentence=origin_sentence,
        ai_sentence=ai_sentence,
        label=label,
        duration=sentence_duration,
    )
    # 插入sentence表
    db.insert_sentence(sentence)


if __name__ == "__main__":
    # 插入interview表
    interview_id = db.insert_interview(0, '', 0)
    s = ["hi, please introduce yourself", "my name is Apple，I am a user of your application",
         "do you have any suggestions for our software?",
         "absolutely yes, your application is so ugly ans speed is so slow",
         "are there any new features you’d like to see",
         "i hope your application can have an ai assistant", "ok, we will develop that, thank you", "stop listening"]
    i = 0
    # 循环处理音频
    while listening:
        listen_and_respond(s[i])
        change_role()
        i += 1
        time.sleep(3)
    # 生成总结
    summary = my_openai.get_interview_resp(origin_sentences)
    # 更新interview表
    db.update_interview(interview_id, summary, total_duration)
