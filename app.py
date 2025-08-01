from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

# JSON faylni yo'li
DATA_FILE = 'data/ratings.json'

# JSON fayl mavjud bo'lmasa, bo'sh holatda yaratamiz
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        show = request.form['show']
        rating = int(request.form['rating'])

        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

        if show not in data:
            data[show] = []

        data[show].append(rating)

        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)

        return redirect('/')

    shows = [
        'RAW - 4 September',
        'SmackDown - 6 September',
        'SummerSlam 2025',
        'WrestleMania 41'
    ]
    return render_template('index.html', shows=shows)