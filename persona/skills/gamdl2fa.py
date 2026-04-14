from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
from dataclasses import dataclass
from urllib3.exceptions import NameResolutionError
import datetime
import logging
import requests
import random
import os
import re

BACKOFF_SEC = 30

class PersonaSkill(PersonaBaseSkill) :
	"""A skill to automatically respond to specific keyword combinations.'"""

	def __init__(self) :
		self.last_check = datetime.datetime.now().timestamp() - BACKOFF_SEC
		self.log = logging.getLogger(__name__)
		self.log = logging.LoggerAdapter(self.log,{'log_module':'gamdl2fa'})

	def startup(self) :
		required_env = ['GAMDL_URL']
		for req in required_env :
			if not os.environ.get(req, None) :
				raise PersonaStartupException(f'Missing required env var \'{req}\'')
		self.gamdl_url = os.environ['GAMDL_URL']

	def match_intent(self,message: Message) -> bool :
		# Skip messages sent with invisible ink
		if re.fullmatch('^[0-9]{6}$', message.text) and message.meta['isFromMe'] :
			# Don't respond if you've responded already recently
			if datetime.datetime.now().timestamp() < (self.last_check + BACKOFF_SEC) :
				self.log.warning('Responding too fast, not responding again.')
				return False
			return True
		return False


	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		self.last_check = datetime.datetime.now().timestamp()
		try :
			try :
				postdata = requests.post(self.gamdl_url, data={'code': message.text},timeout=5)
				if postdata.status_code == 200 :
					response_text = "✅🔒"
				else :
					response_text = "❌🔒"
			except NameResolutionError as e :
					response_text = "❌🔒"
			return persona.Message(
				text=response_text,
				sender_identifier=message.sender_identifier,
				chat_identifier=message.chat_identifier,
				attachments=[],
				timestamp=datetime.datetime.now()+datetime.timedelta(seconds=random.randrange(1,5)),
				recipients=[message.sender_identifier],
				identifier=None,
				meta={}
			)
		except Exception as e :
			raise persona.PersonaResponseException(str(e))
