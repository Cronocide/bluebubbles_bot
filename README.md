# bluebubbles_bot

## A chatbot for a local BlueBlubbles server.

![Build Status](https://jenkins.cronocide.net/buildStatus/icon?job=git.cronocide.net%2Fbluebubbles-bot%2Fmaster&subject=Jenkins%20Build)

## Usage

```
usage: bluebubbles_bot [-h] [-l LOG] [-v]

optional arguments:
  -h, --help         show this help message and exit
  -l LOG, --log LOG  Specify a file to log to.
  -v, --verbose      Include verbose information in the output. Add 'v's for more output.

Example:
	bluebubbles_bot -h
```

bluebubbles_bot loads instances of the `PersonaSkill` class from python files in the [skills](persona/skills) folder.
You may configure the skill by specifying `startup` and `shutdown` functions to configure your skills as required.
It will be helpful to follow the examples in the [skills](persona/skills) folder for designing your skills for the bot.

## Installation

As with most of my software, this can be installed as a python package or a Docker container.

- `pip3 install bluebubbles_bot`
- `docker build -t blue_bubbles_bot .`

## Configuration

The following environment variables must be set to configure the bot:

`BB_SERVER_URL` : The URL of the BlueBubbles server, including protocol and port.

`BB_SERVER_PASSWORD` : The password to the BlueBubbles server.

`BIND_PORT` : The port to bind to to receive callbacks from the BlueBubbles server.

`USE_PRIVATE_API` : Whether or not to use the Private API in BlueBubbles. Default is `false`

## Configuring Skills

Each skill consumes it's own environment variables to configure and run. Here are some of the configurable options for the included skills:

### chatgpt.py

`OPENAI_API_KEY` : The API key to OpenAI, from OpenAI.

`OPENAI_ORGANIZATION` : The Organization ID from OpenAI.

`RESPONSE_PREAMBLE` : Instructions to ChatGPT for how it should respond and behave, given as a preamble for any conversation with it. A default preamble is provided (see [persona/skills/chatgpt.py](chatgpt.py).

## Writing Skills

Writing new skills is simple. Copy a skill from the [persona/skills/](skills) folder to a different name and modify these three functions:

`match_intent` : This should return true if your skill should respond to a message

`respond` : Return a message object to a chat

`generate` : Create a new message object to be sent to a chat

Additional you can use these two functions to start up and shut down your skill:

`startup` : Do any work your skill needs to get ready

`shutdown` : Do any work your skill needs to clean up

## Justification

Initially all I wanted to do was translate Apple Music links to Spotify links and vice-versa. But building platforms is more fun than building tools.
