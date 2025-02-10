from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

ARTICLES_FILE = 'articles.json'

# Load articles from file
def load_articles():
    if os.path.exists(ARTICLES_FILE):
        try:
            with open(ARTICLES_FILE, 'r', encoding='utf-8') as file:
                data = file.read().strip()
                return json.loads(data) if data else []
        except json.JSONDecodeError:
            return []
    return []

# Save articles to file
def save_articles(articles):
    with open(ARTICLES_FILE, 'w', encoding='utf-8') as file:
        json.dump(articles, file, indent=4)

# Generate unique ID
def generate_unique_id(articles):
    if not articles:
        return 1
    existing_ids = {article['id'] for article in articles}
    new_id = 1
    while new_id in existing_ids:
        new_id += 1
    return new_id

# Serve font file from the root directory
@app.route('/KohinoorBangla-Regular.otf')
def serve_font():
    return send_from_directory(os.getcwd(), 'KohinoorBangla-Regular.otf')

@app.route('/')
def home():
    articles = load_articles()
    return render_template('index.html', articles=articles)

@app.route('/article/<int:id>')
def article(id):
    articles = load_articles()
    article = next((a for a in articles if a['id'] == id), None)
    if not article:
        return "Article not found", 404
    return render_template('article.html', article=article)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    articles = load_articles()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_article = {
            'id': generate_unique_id(articles),
            'title': title,
            'content': content
        }
        articles.append(new_article)
        save_articles(articles)
        return redirect(url_for('admin'))

    return render_template('admin.html', articles=articles)

@app.route('/delete/<int:id>')
def delete(id):
    articles = load_articles()
    articles = [a for a in articles if a['id'] != id]
    save_articles(articles)
    return redirect(url_for('admin'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    articles = load_articles()
    article = next((a for a in articles if a['id'] == id), None)

    if not article:
        return "Article not found", 404

    if request.method == 'POST':
        article['title'] = request.form['title']
        article['content'] = request.form['content']
        save_articles(articles)
        return redirect(url_for('admin'))

    return render_template('edit.html', article=article)

if __name__ == '__main__':
    if not os.path.exists(ARTICLES_FILE):
        save_articles([])

    app.run(host='0.0.0.0', port=5000)
