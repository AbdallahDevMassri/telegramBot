FROM python

WORKDIR usr/src/app

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8443

CMD ["python3", "app.py"]