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
		matches = re.search('^Why did the .* cross the road\?', message.text)
		if matches :
			return True
		return False

	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		message.text = 'To get to the other side!'
		return message
