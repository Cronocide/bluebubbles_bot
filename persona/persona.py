from __future__ import annotations
import os
import inspect
import logging
import importlib
from typing import List
from dataclasses import dataclass
import datetime

class LoggingFormatter(logging.Formatter):
	def format(self, record):
		module_max_width = 30
		datefmt='%Y/%m/%d/ %H:%M:%S'
		level = f'[{record.levelname}]'.ljust(9)
		if 'log_module' not in dir(record) :
			modname = str(record.module)+'.'+str(record.name)
		else :
			modname = record.log_module
		modname = (f'{modname}'[:module_max_width-1] + ']').ljust(module_max_width)
		final = "%-7s %s [%s %s" % (self.formatTime(record, self.datefmt), level, modname, record.getMessage())
		return final

class Persona :
	"""A class that represents state data for the chatbot. This is the personality for the bot.
	   Personas load skills that allow them to execute different commands. The personas can receive
	   state data from the skills to affect their current context."""

	_skill_map = {}
	_delegate_map = {}
	_initialized_skills = []
	skill_class = 'Persona'.strip('-').capitalize() + 'Skill'
	skill_class = 'PersonaSkill'
	ready_skills = {}
	def __init__(self) :
		# Enable logging
		self.log = logging.getLogger(__name__)
		self.log = logging.LoggerAdapter(self.log,{'log_module':'persona'})
		logging.getLogger().handlers[0].setFormatter(LoggingFormatter())
		# Load skills
		available_skills = self.search_skills(directory='/'.join(os.path.realpath(__file__).split('/')[:-2]) + '/persona' + '/skills')
		self.use_skills([x for x in available_skills.values()])
		self.startup()

	# loading code
	def add_skill(self,skill,reload) :
		"""Adds a given skill and instance, reinitializing one if it already exists and such is specified."""
		skill_name = skill.__module__.split('.')[-1]
		if not reload and skill_name in self._skill_map.keys():
			pass
		else :
			# We can't startup the skill here because it hasn't been configured. We'll handle that at runtime.
			try:
				# Remove any intialized objects of the same name, forcing a reinitialization
				_initialized_skills.remove(self._skill_map[skill_name])
			except:
				pass
			self._skill_map.update({skill_name:skill})

	def use_skills(self,skills,reload=False) :
		"""Defines skills that should be used in a lookup, optionally forcing them to reload."""
		# Verify data
		if type(skills) != list :
			raise ValueError('argument \'skills\' should be of type list')
		for skill in skills :
			# Check if the skill is a string or a descendent of a persona-skill class
			if type(skill) != str and self.skill_class not in [x.__name__ for x in inspect.getmro(skill)] :
				raise ValueError('unkown type for skill')
			# Find skills by name using a default path
			if type(skill) == str :
				available_skills = [y for x,y in search_skills().items() if x == skill and self.skill_class in [z.__name__ for z in inspect.getmro(y)]]
				if len(available_skills) == 0 :
					raise FileNotFoundError(skill + '.py not found')
				skill = available_skills[0]
			if self.skill_class in [x.__name__ for x in inspect.getmro(skill)] :
				skill_name = skill.__module__.split('.')[-1]
				self.add_skill(skill,reload)
				continue

	def get_skills(self) :
		"""Returns a map of skills configured and loaded."""
		return self._skill_map

	def search_skills(self,directory=None) :
		"""Searches a given directory for compatible skills and returns a map of available skill names and classes."""
		if not directory :
			directory = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + '/' + 'skills'
		directory = os.path.normpath(os.path.expanduser(os.path.expandvars(directory)))
		name_map = {}
		candidates = {x.split('.')[0]:x for x in os.listdir(directory) if x.endswith('.py')}
		for name,filename in candidates.items() :
			try :
				spec = importlib.util.spec_from_file_location(name, directory + '/' + filename)
				mod = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(mod)
				instance = getattr(mod,self.skill_class)
				name_map.update({filename.split('.')[0]:instance})
			except Exception as e :
				# Handle skill loading issues if desired
				print("Unable to load skill from " + filename + ": " + str(e))
		return name_map

	def startup(self) :
		"""Startup all message skill processors"""
		for skill in self._skill_map.keys() :
			ClassInstance = self._skill_map[skill]
			skillinstance = ClassInstance()
			skillinstance.startup()
			self.ready_skills.update({skill:skillinstance})


	def receive_message(self,message: Message) :
		"""Process the receipt of a message."""
		generated_messages = []
		for skill in self.ready_skills.values() :
			should_respond = skill.match_intent(message)
			if should_respond :
				response = skill.respond(message=message)
				if response :
					self.log.info(f'Responding to \'{message.text}\' with \'{response.text}\'')
					generated_messages.append(response)
		return generated_messages
