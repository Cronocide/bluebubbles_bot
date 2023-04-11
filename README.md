# bluebubbles_bot

## A chatbot for a local BlueBlubbles server.

![Build Status](https://jenkins.cronocide.net/job/git.cronocide.net/job/bluebubbles-bot/job/master/badge/icon?subject=Jenkins%20Build)

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

bluebubbles_bot loads instances of the `PersonaSkill` class from python files in the [skills](/skills) folder.
You may configure the skill by specifying `startup` and `shutdown` functions to configure your skills as required.
It will be helpful to follow the examples in the [skills](/skills) folder for designing your skills for the bot.

## Installation

As with most of my software, this can be installed as a python package or a Docker container.

- `pip3 install bluebubbles_bot`
- `docker build -t blue_bubbles_bot .`

## Configuration

The following environment variables must be set to configure the bot:

`BB_SERVER_URL` : The URL of the BlueBubbles server, including protocol and port.

`BB_SERVER_PASSWORD` : The password to the BlueBubbles server.

`USE_PRIVATE_API` : Whether or not to use the Private API in BlueBubbles. Default is `false`



## Justification

Initially all I wanted to do was translate Apple Music links to Spotify links and vice-versa. But building platforms is more fun than building tools.

