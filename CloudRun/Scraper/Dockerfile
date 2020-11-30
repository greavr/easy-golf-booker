from debian

ENV DEBIAN_FRONTEND noninteractive
ENV USER apps
RUN useradd apps

RUN apt-get update
RUN apt-get -y install wget zip python3 python3-pip
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -y ./google-chrome-stable_current_amd64.deb

RUN wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip && unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/bin/chromedriver
RUN chown root:root /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

COPY /code /app
WORKDIR /app

RUN pip3 install -r requirements.txt

USER apps

EXPOSE 8080

CMD ["python3","main.py"]