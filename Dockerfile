FROM python:3.12 as PYTHON
ENV PROJ_NAME=bluebubbles_bot

# Copy project files
ADD ./ /$PROJ_NAME

RUN pip3 install /$PROJ_NAME

# Run entrypoint
ENTRYPOINT ["/usr/local/bin/bluebubbles_bot","-vvv"]
