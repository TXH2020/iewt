from flask import *

app=Flask(__name__)

@app.get('/test')
def get():
    #only to test whether service is alive or not.
    return "ok"

@app.post('/command')
def post():
    #implement database code here
    return "inserted"

if __name__=='__main__':
    app.run()
