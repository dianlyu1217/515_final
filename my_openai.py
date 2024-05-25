import json

import openai
import db
import os
from typing import Tuple, List
from dotenv import load_dotenv
import csv

# 设置OpenAI API键和自定义ChatGPT角色
load_dotenv()
openai.api_key = os.getenv('openai_key')
label_sample = []
sentence_system_msg = {"role": "system",
                       "content": "I'm doing an interview with a friend and I'm going to upload something a person said recently. First you have to study the example I gave you earlier, which shows which types of words should be labeled with which ones. What you need to do next is: 1. Generate a summary of less than 20 words based on this paragraph. 2. Based on what you have learned and your own understanding, generate the appropriate label for this paragraph, the label can only be selected from the previous examples. Note that I'm not talking to you, you just return what I need as requested. The format of the returned content must be in the format of Summary: xxx, Label: xxx", }
sentence_summary_system_msg = {"role": "system", "content": "Generate a summary of less than 30 words based on our conversation below"}
interview_system_msg = {"role": "system", "content": "I will send you an interview conversation, and you need to give me a summary within 100 words based on all the conversation content."}

tag_system_msg = {"role": "system",
                  "content": "I'll pass you an interview conversation, and each sentence has been tagged the same. You need to return to me a summary within 100 words based on all the conversation content."}


class LabelSample:
    def __init__(self, sentence, label):
        self.sentence = sentence
        self.label = label

    def to_dict(self):
        return {'sentence': self.sentence, 'label': self.label}


def get_label_sample() -> List[LabelSample]:
    if len(label_sample) > 0:
        return label_sample
    with open('label_sample.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row if there is one
        for row in reader:
            if len(row) >= 2:  # Ensure there are at least two columns
                sample = LabelSample(sentence=row[0], label=row[1])
                label_sample.append(sample)


def get_sentence_resp(origin_sentence: str) -> Tuple[str, str]:
    try:
        get_label_sample()
        sentence_msg = [{"role": "system", "content": json.dumps([sample.to_dict() for sample in label_sample])}, sentence_system_msg]
        sentence_msg.append({"role": "user", "content": origin_sentence})
        resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=sentence_msg)
        chatgpt_reply = resp["choices"][0]["message"]["content"]
        print(chatgpt_reply)

        try:
            summary = chatgpt_reply.split("Summary: ")[1].split("Label: ")[0]
        except Exception as e1:
            summary = ''
        try:
            label = chatgpt_reply.split("Label: ")[1]
        except Exception as e2:
            label = ''
        return summary, label
    except Exception as e:
        print("Failed to get response from OpenAI: " + str(e))
        return '', ''


def get_interview_resp(origin_sentences: List[str]) -> str:
    try:
        interview_msg = [interview_system_msg]
        for origin_sentence in origin_sentences:
            interview_msg.append({"role": "user", "content": origin_sentence})
        resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=interview_msg)
        interview_summary = resp["choices"][0]["message"]["content"]
        print(interview_summary)
        return interview_summary
    except Exception as e:
        print("Failed to get response from OpenAI: " + str(e))
        return ''


def get_tag_summary(sentences: List[db.SentenceData]) -> str:
    try:
        tag_msg = [tag_system_msg]
        for sentence in sentences:
            tag_msg.append({"role": "user", "content": sentence.origin_sentence})
        resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=tag_msg)
        tag_summary = resp["choices"][0]["message"]["content"]
        print(tag_summary)
        return tag_summary
    except Exception as e:
        print("Failed to get response from OpenAI: " + str(e))
        return ''


def get_summary(origin_sentences: List[str]) -> str:
    try:
        interview_msg = [sentence_summary_system_msg]
        for origin_sentence in origin_sentences:
            interview_msg.append({"role": "user", "content": origin_sentence})
        resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=interview_msg)
        sentence_summary = resp["choices"][0]["message"]["content"]
        print(sentence_summary)
        return sentence_summary
    except Exception as e:
        print("Failed to get response from OpenAI: " + str(e))
        return ''
