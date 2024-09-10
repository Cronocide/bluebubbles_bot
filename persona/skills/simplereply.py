from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
from dataclasses import dataclass
import datetime
import logging
import random
import os
import re

BACKOFF_SEC = 10
SIMPLE_REPLIES = {
	'^😘🍕$': ['😘🍕'],
	'^🍕😘$': ['😘🍕'],
	'^Why did the .* cross the road\?': ['To get to the other side!'],
	'^Hello$': ['Hello!','Howdy!','Hello there!','What\'s up!','Hi there!']
}
class PersonaSkill(PersonaBaseSkill) :
	"""A skill to automatically respond to specific keyword combinations.'"""

	def __init__(self) :
		self.last_check = datetime.datetime.now().timestamp() - BACKOFF_SEC
		self.log = logging.getLogger(__name__)
		self.log = logging.LoggerAdapter(self.log,{'log_module':'simplereply'})

	def match_intent(self,message: Message) -> Bool :
		# Don't respond if you've responded already recently
		if datetime.datetime.now().timestamp() < (self.last_check + BACKOFF_SEC) :
			self.log.warn('Responding too fast, not responding again.')
			return False
		for trigger in SIMPLE_REPLIES.keys() :
			matches = re.search(trigger, message.text)
			if matches :
				return True
		return False


	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		try :
			for trigger in SIMPLE_REPLIES.keys() :
				matches = re.search(trigger, message.text)
				if matches :
					response_options = SIMPLE_REPLIES[trigger]
					break
			response_text = random.choice(response_options)
			response = SIMPLE_REPLIES[message.text]
			return persona.Message(
				text=response,
				sender_identifier=message.sender_identifier,
				chat_identifier=message.chat_identifier,
				attachments=[],
				timestamp=datetime.datetime.now()+datetime.timedelta(seconds=random.randrange(5,15)),
				recipients=[message.sender_identifier],
				identifier=None,
				meta={}
			)
		except Exception as e :
			raise persona.PersonaResponseException(str(e))
