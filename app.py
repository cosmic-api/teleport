from flask import Flask
import teleport

app = Flask(__name__)

@app.route("/")
def hello():
    return repr(teleport._ctx_stack.top)

class T(teleport.TypeMap):
    pass

class TeleportMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        with T():
            return self.app(environ, start_response)

if __name__ == "__main__":
    app.wsgi_app = TeleportMiddleware(app.wsgi_app)
    app.run(debug=True)
