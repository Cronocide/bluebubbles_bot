from __future__ import annotations
from persona.persona import *
import abc
import os
import inspect
import importlib
from typing import List
from dataclasses import dataclass
import datetime
class PersonaException(Exception) :
	"""The base Persona exception class."""

class PersonaStartupException(PersonaException) :
	"""The Persona exception class to raise during startup failures."""

class PersonaIntentException(PersonaException) :
	"""The Persona exception class to raise it cannot be determined if the skill should be matched."""

class PersonaResponseException(PersonaException) :
	"""The Persona exception class to raise when a response cannot be generated."""

@dataclass
class Attachment :
    """Basic information about attachments in the messages the persona will receive."""
    mime_type: str
    data: any

@dataclass
class Message :
	"""Basic information about the messages the persona will receive. Types are simple
	   for simplicity and flexibility."""
	sender_identifier: str
	chat_identifier: str
	text: str
	attachments: List[Attachment]
	timestamp: datetime.datetime
	recipients: List[String]
	identifier: str
	meta: dict


class PersonaBaseSkill() :
	"""The base class for a Persona skill."""

	def __init__(self) :
		self.context = {}

	def startup(self) :
		"""Perform any initialization actions, such as searching the environment for config or logging into services.
		   This action should raise PersonaStartupException on failure."""
		pass

	def shutdown(self) :
		"""Perform any shutdown and cleanup actions, such as searching logging out of online services or removing
		   temporary secrets. Exceptions raised here are ignored."""
		pass

	def match_intent(self,message: Message) -> Bool :
		"""Receive text and determine if the skill should be used to respond to the message."""
		raise PersonaIntentException('This skill does not know if it should respond.')

	def respond(self, message: Message) -> Message :
		"""Respond to a message by generating another message.
		   This is called after the intent has been matched and the skill should produce a response.
		   The Persona may modify the message, including its recipients, timestamp, or content."""
		raise PersonaResponseException('This skill is not implemented to respond.')
