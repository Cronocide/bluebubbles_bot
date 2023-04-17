from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
import datetime
import logging
import re

BACKOFF_SEC = 30

class PersonaSkill(PersonaBaseSkill) :
	"""A simple test skill that responds to the joke 'Why did ____ cross the road?''"""

	def __init__(self) :
		self.last_check = datetime.datetime.now().timestamp() - BACKOFF_SEC
		self.log = logging.getLogger(__name__)
		self.log = logging.LoggerAdapter(self.log,{'log_module':'chicken'})

	def match_intent(self,message: Message) -> Bool :
		# Don't respond if you've responded already recently
		if datetime.datetime.now().timestamp() < (self.last_check + BACKOFF_SEC) :
			self.log.warn('Responding too fast, not responding again.')
			return False
		matches = re.search('^Why did the .* cross the road\?', message.text)
		if matches :
			return True
		return False

	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		return persona.Message(text='To get to the other side!',sender_identifier=message.sender_identifier,chat_identifier=message.chat_identifier,attachments=[],timestamp=datetime.datetime.now(), recipients=[message.sender_identifier], identifier=None, meta={})
