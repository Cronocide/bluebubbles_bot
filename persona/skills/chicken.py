from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
import datetime
import re

class PersonaSkill(PersonaBaseSkill) :
	"""A simple test skill that responds to the joke 'Why did ____ cross the road?''"""
	def match_intent(self,message: Message) -> Bool :
		matches = re.search('^Why did the .* cross the road\?', message.text)
		if matches :
			return True
		return False

	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message."""
		message.text = 'To get to the other side!'
		return message
