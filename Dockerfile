# Don't Remove Credit 
# Subscribe YouTube Channel For Amazing Bot 
# Ask Doubt on telegram 

FROM python:3.10.8-slim-buster

RUN apt update && apt upgrade -y
RUN apt install git -y
COPY requirements.txt /requirements.txt

RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /app
WORKDIR /app
COPY . /app
CMD ["python", "bot.py"]
