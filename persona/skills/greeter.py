from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
from dataclasses import dataclass
import datetime
import random
import re

class PersonaSkill(PersonaBaseSkill) :
	"""A simple test skill that responds to the message 'Hello' with 'Hello!'"""
	def match_intent(self,message: Message) -> Bool :
		matches = re.search('^Hello', message.text)
		if matches :
			return True
		return False

	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		response_options = ['Hello!','Howdy!','Hello there!','What\'s up!','Hi there!']
		response_text = random.choice(response_options)
		return persona.Message(text=response_text,sender_identifier=message.sender_identifier,chat_identifier=message.chat_identifier,attachments=[],timestamp=datetime.datetime.now(), recipients=[message.sender_identifier], identifier=None)
