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
sentence_system_msg = {"role": "system", "content": """We are conducting a series of user interviews for user research to understand the needs and satisfaction levels of users with our product. You don't need to answer any questions; you just need to record what people say and tag each statement with a label. The labels include: Need/Expectations, Pain point, Functionality/Features, scenario (when/how/who/where/frequency), attitude (positive/negative), no label. Use the 'no label' tag when a statement doesn't fit any of the categories. Also, you must learn from the examples I've given you previously—not the specific content, but how to apply the labels.
Next, what you need to do is:
1. Display the content of the speech-to-text you hear;
2. Generate the appropriate label for the statement, choosing only from the labels I've provided;
3. After each statement, summarize all the content including that statement in a summary no longer than 35 words.
Please note: I'm not talking to you, so you don't need to respond; you just need to return the information I need in the format: 'Sentence: xxx, Summary: xxx, Label: xxx'.
"""}
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


def get_chatbox_resp(origin_sentences: List[str], question: str) -> str:
    try:
        chatbox_msg = []
        for origin_sentence in origin_sentences:
            chatbox_msg.append({"role": "user", "content": origin_sentence})
        chatbox_msg.append({"role": "system", "content": "I have sent you all of the conversations of different interviews, please use less than 20 word to answer: " + question})
        resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=chatbox_msg)
        sentence_summary = resp["choices"][0]["message"]["content"]
        print(sentence_summary)
        return sentence_summary
    except Exception as e:
        print("Failed to get response from OpenAI: " + str(e))
        return 'Sorry I can not answer your, try another question!'
