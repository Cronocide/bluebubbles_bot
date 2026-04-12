from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
from dataclasses import dataclass
import datetime
import logging
import requests
import random
import os
import re

BACKOFF_SEC = 10

class PersonaSkill(PersonaBaseSkill) :
	"""A skill to automatically respond to specific keyword combinations.'"""

	def __init__(self) :
		self.last_check = datetime.datetime.now().timestamp() - BACKOFF_SEC
		self.log = logging.getLogger(__name__)
		self.log = logging.LoggerAdapter(self.log,{'log_module':'gamdl2fa'})

	def startup() :
		required_env = ['GAMDL_URL']
		for req in required_env :
			if not os.environ.get(req, None) :
				raise PersonaStartupException(f'Missing required env var \'{req}\'')
		self.gamdl_url = os.environ['GAMDL_URL']

	def match_intent(self,message: Message) -> bool :
		# Skip messages sent with invisible ink
		if re.fullmatch('^[0-9]{6}$', message.text) :
			return True
		# Don't respond if you've responded already recently
		if datetime.datetime.now().timestamp() < (self.last_check + BACKOFF_SEC) :
			self.log.warning('Responding too fast, not responding again.')
			return False
		return False


	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		self.last_check = datetime.datetime.now().timestamp()
		try :
			requests.post(self.gamdl_url, data={'code': message.text},timeout=5)
		except Exception as e :
			raise persona.PersonaResponseException(str(e))
