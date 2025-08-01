from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

ratings = []

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        show_name = request.form["show"]
        rating = float(request.form["rating"])
        ratings.append((show_name, rating))
        return redirect(url_for("home"))
    
    average = round(sum(r[1] for r in ratings) / len(ratings), 2) if ratings else None
    return render_template("index.html", ratings=ratings, average=average)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)