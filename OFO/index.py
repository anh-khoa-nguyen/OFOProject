from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('Restaurant/ResLogin.html')
@app.route('/reslogin')
def login():
    return render_template('Restaurant/ResLogin.html')

@app.route('/resregister')
def register():
    return render_template('Restaurant/ResRegister.html')
if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)