from flask import Flask, request, render_template_string

app = Flask(__name__)

comments = []

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Comment Board</title></head>
    <body>
        <h1>Comments</h1>
        <form method="POST" action="/comment">
            <input type="text" name="comment" placeholder="Add a comment">
            <button type="submit">Post</button>
        </form>
        <div id="comments">
            {% for comment in comments %}
                <div class="comment">{{ comment | safe }}</div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, comments=comments)

@app.route('/comment', methods=['POST'])
def add_comment():
    comment = request.form.get('comment', '')
    comments.append(comment)
    return index()

@app.route('/search')
def search():
    query = request.args.get('q', '')
    html = f"<h1>Search results for: {query}</h1>"
    return html

if __name__ == '__main__':
    app.run(debug=True)
