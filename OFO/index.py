from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/tim-kiem")
def tim_kiem():
    return render_template('tim-kiem.html')

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)