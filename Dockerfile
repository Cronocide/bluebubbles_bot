FROM ubuntu
ENV PROJ_NAME=python-tool

# Install Python
FROM python:3.10.6 as PYTHON

# Copy project files
ADD ./ /$PROJ_NAME

# Run entrypoint
ENTRYPOINT [""]
