import os
from flask import Flask, flash, render_template, redirect, request

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', "super-secret")


#@app.route('/')
#def main():
#    return render_template('main.html')

@app.route('/')
def hello_world():
    return 'Hello, World!'

