import openai
import db
import os
from typing import Tuple, List
from dotenv import load_dotenv

# 设置OpenAI API键和自定义ChatGPT角色
load_dotenv()
openai.api_key = os.getenv('openai_key')

sentence_system_msg = {"role": "system",
                       "content": "My friend and I were doing an interview, and we would take turns typing what we were going to say. Every time one of us finishes speaking, you need to do two things: 1. Produce a summary of what we said within 20 words; 2. Choose from the three tags [Pain Points, Needs, and Functionality] A tag that best fits the current paragraph; 3. The format you return each time must conform to the template and remain fixed. The style is [Summary: xxx, Label: xxx]",
                       }
interview_system_msg = {"role": "system",
                        "content": "I will send you an interview conversation, and you need to give me a summary within 100 words based on all the conversation content."}

tag_system_msg = {"role": "system",
                  "content": "I'll pass you an interview conversation, and each sentence has been tagged the same. You need to return to me a summary within 100 words based on all the conversation content."}


def get_sentence_resp(origin_sentences: List[str]) -> Tuple[str, str]:
    try:
        sentence_msg = [sentence_system_msg]
        for origin_sentence in origin_sentences:
            sentence_msg.append({
                "role": "user",
                "content": origin_sentence
            })
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=sentence_msg
        )
        chatgpt_reply = resp["choices"][0]["message"]["content"]
        print(chatgpt_reply)

        summary = chatgpt_reply.split("Summary: ")[1].split(", Label: ")[0]
        label = chatgpt_reply.split("Label: ")[1]
        return summary, label

        # tag_index = chatgpt_reply.find("标签:")
        # 提取总结内容，假设总结部分总是从开始到“标签:”关键字前
        # ai_sentence = chatgpt_reply[3:tag_index].strip() if tag_index != -1 else chatgpt_reply[3:].strip()
        # 提取标签内容，从“标签:”开始到字符串末尾
        # tag = chatgpt_reply[tag_index + 3:].strip() if tag_index != -1 else ""
        # return ai_sentence, tag
    except Exception as e:
        print("Failed to get response from OpenAI: " + str(e))
        return "Failed to get response from OpenAI: " + str(e), ''


def get_interview_resp(origin_sentences: List[str]) -> str:
    try:
        interview_msg = [interview_system_msg]
        for origin_sentence in origin_sentences:
            interview_msg.append({
                "role": "user",
                "content": origin_sentence
            })
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=interview_msg
        )
        interview_summary = resp["choices"][0]["message"]["content"]
        print(interview_summary)
        return interview_summary
    except Exception as e:
        return "Failed to get response from OpenAI: " + str(e)


def get_tag_summary(sentences: List[db.SentenceData]) -> str:
    try:
        tag_msg = [tag_system_msg]
        for sentence in sentences:
            tag_msg.append({
                "role": "user",
                "content": sentence.origin_sentence
            })
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=tag_msg
        )
        tag_summary = resp["choices"][0]["message"]["content"]
        print(tag_summary)
        return tag_summary
    except Exception as e:
        return "Failed to get response from OpenAI: " + str(e)
