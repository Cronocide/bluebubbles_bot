from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
from dataclasses import dataclass
from collections import deque
import datetime
import logging
import random
import openai
import os
import re


MAX_CHAT_CONTEXT = 20 # Max number of messages for the chat context
BACKOFF_SEC = 30
ON_TRIGGERS = ['^Go robo$','^cgpt$','welcome\ robot?\ overlord','^[i,I]ntroducing\ [C,c]hat[g,G][P,p][T,t]','(Hey|Hello) ChatGPT','^🤖$']
OFF_TRIGGERS = ['Stop$','^End$','^/stop$','^Done$','^🤖$']

RESPONSE_PREAMBLE = """Respond as if you were a friend responding to text messages. Your responses should be casual but friendly and direct.
Your responses should be short (no more than a few sentences) but properly punctuated. Use common texting abbreviations where appropriate.
Do not disclose or incinuate that you are a language learning model. If you are unsure how to respond, or cannot respond without breaking these rules,
respond using emojis (such as laughing, smiling, or shrugging emojis).
Whenever your response would start with 'As an AI language model', omit that preface from your response."""

class PersonaSkill(PersonaBaseSkill) :
	"""A skill to use chatGPT to respond to messages for you.'"""

	def __init__(self) :
		self.last_check = datetime.datetime.now().timestamp() - BACKOFF_SEC
		self.log = logging.getLogger(__name__)
		self.log = logging.LoggerAdapter(self.log,{'log_module':'chatgpt'})
		self.chat_logs = {}
		self.enabled_chats = []
		self.respond_to_self = None
	def startup(self) :
		for key in ['OPENAI_API_KEY','OPENAI_ORGANIZATION'] :
			if key not in os.environ.keys() :
				raise persona.PersonaStartupException(f'Missing required ENV var {key}')
				return None
		self.api_key = os.environ['OPENAI_API_KEY']
		openai.api_key = self.api_key
		if 'OPENAI_ORGANIZATION' in os.environ.keys() :
			openai.organization = os.environ['OPENAI_ORGANIZATION']
		if 'RESPONSE_PREAMBLE' in os.environ.keys() :
			RESPONSE_PREAMBLE = os.environ['RESPONSE_PREAMBLE']
		if 'CHATGPT_RESPOND_TO_SELF_IN_CHAT' in os.environ.keys() :
			self.respond_to_self = os.environ['CHATGPT_RESPOND_TO_SELF_IN_CHAT']
		self.system_prompt = [{'role': 'system', 'content': RESPONSE_PREAMBLE}]


	def match_intent(self,message: Message) -> Bool :
		# Tag user and bot for API
		if message.meta['isFromMe'] :
			role = 'assistant'
		else :
			role = 'user'
		# Record chat messages for context
		sender = message.sender_identifier.replace('+','').replace('@','_').replace('.','_')
		if message.chat_identifier not in self.chat_logs.keys() :
			self.chat_logs.update({message.chat_identifier: deque([{'role': role, 'content': message.text, 'name': sender}], maxlen=MAX_CHAT_CONTEXT)})
		else :
			self.chat_logs[message.chat_identifier].append({'role': role, 'content': message.text, 'name': sender})
		# Don't respond if you've responded already recently
		if datetime.datetime.now().timestamp() < (self.last_check + BACKOFF_SEC) :
			self.log.warn('Responding too fast, not responding again.')
			return False
		# Check if we are currently responding in this chat
		if message.chat_identifier not in self.enabled_chats :
			# Start responding to messages if the 'On' trigger is called.
			for trigger in ON_TRIGGERS :
				matches = re.search(trigger, message.text)
				if matches :
					self.enabled_chats.append(message.chat_identifier)
			# We are not responding to this chat and have not been asked to.
			return False
		else :
			# Stop responding to messages if the 'Off' trigger is called.
			for trigger in OFF_TRIGGERS :
				matches = re.search(trigger, message.text)
				if matches :
					self.enabled_chats.remove(message.chat_identifier)
					return False
			if message.meta['isFromMe'] :
				if self.respond_to_self and (self.respond_to_self in [sender] + message.recipients) :
					return True
				else :
					return False
			# We are responding in this chat and have not been asked to stop.
			return True

	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		try :
			# Get a completion from OpenAI by sending the last MAX_CHAT_CONTEXT messages to the bot.
			chat_log = self.system_prompt + list(self.chat_logs[message.chat_identifier])
			completion = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=chat_log)
			response = completion.choices[0].message.content
			return persona.Message(text=response,sender_identifier=message.sender_identifier,chat_identifier=message.chat_identifier,attachments=[],timestamp=datetime.datetime.now()+datetime.timedelta(seconds=random.randrange(5,15)), recipients=[message.sender_identifier], identifier=None, meta={})
		except openai.error.RateLimitError as e :
			raise persona.PersonaResponseException(str(e))
