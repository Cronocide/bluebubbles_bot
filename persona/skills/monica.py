from __future__ import annotations
from typing import List
import persona
from persona import PersonaBaseSkill
from dataclasses import dataclass
import datetime
import logging
import requests
import os
import re

# Vibe-coded with claude-4.6-opus-high. on 2026-02-21.
DEFAULT_CONVERSATION_TIMEOUT = 21600 # 6 hours in seconds
DEFAULT_CONTACT_FIELD_TYPE_NAMES = 'Phone,Email'

class PersonaSkill(PersonaBaseSkill) :
	"""A skill to track iMessage conversations in Monica CRM for contacts with matching phone numbers or email addresses."""

	def __init__(self) :
		self.log = logging.getLogger(__name__)
		self.log = logging.LoggerAdapter(self.log,{'log_module':'monica'})
		self.contact_map = {}
		self.active_conversations = {}
		self.contact_field_types = {}
		self.api_url = None
		self.api_headers = {}
		self.conversation_timeout = DEFAULT_CONVERSATION_TIMEOUT

	def startup(self) :
		for key in ['MONICA_API_URL','MONICA_API_TOKEN'] :
			if key not in os.environ.keys() :
				raise persona.PersonaStartupException(f'Missing required ENV var {key}')
		self.api_url = os.environ['MONICA_API_URL'].rstrip('/')
		self.api_headers = {
			'Authorization': f'Bearer {os.environ["MONICA_API_TOKEN"]}',
			'Content-Type': 'application/json'
		}
		if 'MONICA_CONVERSATION_TIMEOUT' in os.environ.keys() :
			self.conversation_timeout = int(os.environ['MONICA_CONVERSATION_TIMEOUT'])
		# Resolve the contact field types for conversations (phone and email by default)
		field_type_names = DEFAULT_CONTACT_FIELD_TYPE_NAMES
		if 'MONICA_CONTACT_FIELD_TYPES' in os.environ.keys() :
			field_type_names = os.environ['MONICA_CONTACT_FIELD_TYPES']
		self.contact_field_types = self._resolve_contact_field_types(field_type_names)
		if not self.contact_field_types :
			raise persona.PersonaStartupException(f'Could not find any contact field types for "{field_type_names}" in Monica')
		# Populate the contact map with phone number and email to contact ID mappings
		self._populate_contact_map()
		self.log.info(f'Loaded {len(self.contact_map)} contact address mappings from Monica')

	def _api_get(self,endpoint,params=None) :
		"""Make a GET request to the Monica API."""
		url = f'{self.api_url}/{endpoint.lstrip("/")}'
		response = requests.get(url,headers=self.api_headers,params=params)
		response.raise_for_status()
		return response.json()

	def _api_post(self,endpoint,data) :
		"""Make a POST request to the Monica API."""
		url = f'{self.api_url}/{endpoint.lstrip("/")}'
		response = requests.post(url,headers=self.api_headers,json=data)
		response.raise_for_status()
		return response.json()

	def _normalize_address(self,address) :
		"""Normalize an address for consistent lookups. Emails are lowercased, phone numbers are stripped to digits."""
		if '@' in address :
			return address.strip().lower()
		return re.sub(r'[^\d]','',address)

	def _resolve_contact_field_types(self,names) :
		"""Find the contact field type IDs for a comma-separated list of type names."""
		requested = [n.strip().lower() for n in names.split(',')]
		resolved = {}
		try :
			page = 1
			while True :
				result = self._api_get('contactfieldtypes',params={'page': page})
				for field_type in result.get('data',[]) :
					if field_type['name'].lower() in requested :
						resolved[field_type['id']] = field_type['name']
				if page >= result.get('meta',{}).get('last_page',1) :
					break
				page += 1
		except Exception as e :
			self.log.error(f'Failed to resolve contact field types: {e}')
		return resolved

	def _populate_contact_map(self) :
		"""Fetch all contacts and their phone numbers and email addresses from Monica to build the contact map."""
		try :
			page = 1
			while True :
				result = self._api_get('contacts',params={'page': page})
				for contact in result.get('data',[]) :
					contact_id = contact['id']
					contact_name = contact.get('complete_name','Unknown')
					try :
						fields = self._api_get(f'contacts/{contact_id}/contactfields')
						for field in fields.get('data',[]) :
							field_type_id = field.get('contact_field_type',{}).get('id')
							if field_type_id in self.contact_field_types :
								normalized = self._normalize_address(field['content'])
								if normalized :
									self.contact_map[normalized] = {
										'contact_id': contact_id,
										'name': contact_name,
										'contact_field_type_id': field_type_id
									}
									self.log.debug(f'Mapped {normalized} to contact {contact_name} ({contact_id})')
					except Exception as e :
						self.log.warning(f'Failed to fetch contact fields for {contact_name}: {e}')
				if page >= result.get('meta',{}).get('last_page',1) :
					break
				page += 1
		except Exception as e :
			self.log.error(f'Failed to populate contact map: {e}')

	def _resolve_contact_address(self,message) :
		"""Extract the other party's address from a message."""
		if message.meta.get('isFromMe') :
			if len(message.recipients) > 0 :
				return message.recipients[0]
		else :
			return message.sender_identifier
		return None

	def _get_recent_monica_conversation(self,contact_id) :
		"""Check Monica for a recent conversation with this contact within the timeout window."""
		try :
			result = self._api_get(f'contacts/{contact_id}/conversations')
			conversations = result.get('data',[])
			if not conversations :
				return None
			# Find the most recent conversation by latest message timestamp
			most_recent = None
			most_recent_time = None
			for conversation in conversations :
				for msg in conversation.get('messages',[]) :
					written_at = datetime.datetime.fromisoformat(msg['written_at'].replace('Z','+00:00'))
					written_at = written_at.timestamp()
					if most_recent_time is None or written_at > most_recent_time :
						most_recent_time = written_at
						most_recent = conversation
			if most_recent and most_recent_time :
				if (datetime.datetime.now().timestamp() - most_recent_time) < self.conversation_timeout :
					return most_recent
		except Exception as e :
			self.log.warning(f'Failed to fetch conversations from Monica for contact {contact_id}: {e}')
		return None

	def _create_conversation(self,contact_id,contact_field_type_id,happened_at) :
		"""Create a new conversation in Monica for the given contact."""
		try :
			data = {
				'happened_at': happened_at.strftime('%Y-%m-%d'),
				'contact_field_type_id': contact_field_type_id,
				'contact_id': contact_id
			}
			result = self._api_post('conversations',data)
			conversation_id = result['data']['id']
			self.log.info(f'Created new Monica conversation {conversation_id} for contact {contact_id}')
			return conversation_id
		except Exception as e :
			self.log.error(f'Failed to create conversation in Monica: {e}')
		return None

	def _add_message_to_conversation(self,conversation_id,contact_id,content,written_at,is_from_me) :
		"""Add a message to an existing conversation in Monica."""
		try :
			data = {
				'contact_id': contact_id,
				'written_at': written_at.strftime('%Y-%m-%d'),
				'written_by_me': is_from_me,
				'content': content
			}
			self._api_post(f'conversations/{conversation_id}/messages',data)
		except Exception as e :
			self.log.error(f'Failed to add message to Monica conversation {conversation_id}: {e}')

	def _track_conversation(self,contact_id,contact_field_type_id,message) :
		"""Track a message as part of a conversation in Monica for the given contact."""
		is_from_me = message.meta.get('isFromMe',False)
		now = datetime.datetime.now().timestamp()
		content = message.text or ''
		if not content.strip() :
			return
		# Check local cache for an active conversation within the timeout window
		cached = self.active_conversations.get(contact_id)
		if cached :
			elapsed = now - cached['last_message_at']
			if elapsed < self.conversation_timeout :
				# Still within timeout, add to existing conversation
				self._add_message_to_conversation(
					cached['conversation_id'],contact_id,content,message.timestamp,is_from_me
				)
				self.active_conversations[contact_id]['last_message_at'] = now
				return
		# No valid local cache — corroborate with Monica API
		recent = self._get_recent_monica_conversation(contact_id)
		if recent :
			conversation_id = recent['id']
			self.log.info(f'Resuming Monica conversation {conversation_id} for contact {contact_id}')
		else :
			conversation_id = self._create_conversation(contact_id,contact_field_type_id,message.timestamp)
			if not conversation_id :
				return
		# Add the message to the conversation
		self._add_message_to_conversation(conversation_id,contact_id,content,message.timestamp,is_from_me)
		# Update local cache
		self.active_conversations[contact_id] = {
			'conversation_id': conversation_id,
			'last_message_at': now
		}

	def match_intent(self,message: Message) -> bool :
		# Skip messages sent with invisible ink
		if message.data.get('expressiveSendStyleId','') == 'com.apple.MobileSMS.expressivesend.invisibleink' :
			return False
		# Resolve the contact address from the message
		address = self._resolve_contact_address(message)
		if not address :
			return False
		normalized = self._normalize_address(address)
		if normalized not in self.contact_map :
			return False
		# Track the conversation for this Monica contact
		contact_info = self.contact_map[normalized]
		try :
			self._track_conversation(contact_info['contact_id'],contact_info['contact_field_type_id'],message)
		except Exception as e :
			self.log.error(f'Error tracking conversation for {contact_info["name"]}: {e}')
		# Never respond — this skill only tracks conversations silently
		return False

	def respond(self,message: Message) -> Message :
		"""This skill does not respond to messages."""
		return None
