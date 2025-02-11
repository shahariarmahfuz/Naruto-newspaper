from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import json
import os
import time
import requests
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# ফাইল পাথ সংজ্ঞায়িত করুন
ARTICLES_FILE = 'articles.json'
VIDEOS_FILE = 'videos.json'

# আর্টিকেল লোড এবং সেভ করার ফাংশন
def load_articles():
    if os.path.exists(ARTICLES_FILE):
        try:
            with open(ARTICLES_FILE, 'r', encoding='utf-8') as file:
                data = file.read().strip()
                return json.loads(data) if data else []
        except json.JSONDecodeError:
            return []
    return []

def save_articles(articles):
    with open(ARTICLES_FILE, 'w', encoding='utf-8') as file:
        json.dump(articles, file, indent=4)

def generate_unique_id(articles):
    if not articles:
        return 1
    existing_ids = {article['id'] for article in articles}
    new_id = 1
    while new_id in existing_ids:
        new_id += 1
    return new_id

# ভিডিও লোড এবং সেভ করার ফাংশন
def load_videos():
    if os.path.exists(VIDEOS_FILE):
        try:
            with open(VIDEOS_FILE, 'r', encoding='utf-8') as file:
                data = file.read().strip()
                return json.loads(data) if data else []
        except json.JSONDecodeError:
            return []
    return []

def save_videos(videos):
    with open(VIDEOS_FILE, 'w', encoding='utf-8') as file:
        json.dump(videos, file, indent=4)

def generate_video_id(videos):
    if not videos:
        return 1
    return max(video['id'] for video in videos) + 1

# রুটস
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

@app.route('/video')
def video_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    
    videos = load_videos()
    # নতুন ভিডিও প্রথমে দেখানোর জন্য সর্টিং
    videos.sort(key=lambda x: x['id'], reverse=True)
    
    # সার্চ ফিল্টার
    if search_query:
        search_lower = search_query.lower()
        videos = [v for v in videos if search_lower in v['title'].lower() or search_lower in v.get('description', '').lower()]
    
    # পেজিনেশন লজিক
    per_page = 5
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_videos = videos[start_idx:end_idx]
    
    total_pages = (len(videos) + per_page - 1) // per_page
    
    return render_template('videos.html', 
                         videos=paginated_videos,
                         page=page,
                         total_pages=total_pages,
                         search_query=search_query)

@app.route('/video/<int:id>')
def video_player(id):
    videos = load_videos()
    video = next((v for v in videos if v['id'] == id), None)
    if not video:
        return "Video not found", 404
    return render_template('video.html', video=video)

@app.route('/ad_video', methods=['GET', 'POST'])
def video_admin():
    if request.method == 'POST':
        title = request.form['title']
        video_link = request.form['video_link']
        thumbnail_link = request.form.get('thumbnail_link', '')  # থাম্বনেল লিংক (অপশনাল)
        description = request.form.get('description', '')  # ডিসক্রিপশন (অপশনাল)
        videos = load_videos()
        new_video = {
            'id': generate_video_id(videos),
            'title': title,
            'link': video_link,
            'thumbnail': thumbnail_link,
            'description': description
        }
        videos.append(new_video)
        save_videos(videos)
        return redirect(url_for('video_admin'))
    
    videos = load_videos()
    return render_template('ad_video.html', videos=videos)

@app.route('/delete_video/<int:id>')
def delete_video(id):
    videos = load_videos()
    videos = [v for v in videos if v['id'] != id]
    save_videos(videos)
    return redirect(url_for('video_admin'))

@app.route('/ed_video/<int:id>', methods=['GET', 'POST'])
def edit_video(id):
    videos = load_videos()
    video = next((v for v in videos if v['id'] == id), None)
    
    if not video:
        return "Video not found", 404
    
    if request.method == 'POST':
        video['title'] = request.form['title']
        video['link'] = request.form['video_link']
        video['thumbnail'] = request.form.get('thumbnail_link', '')  # থাম্বনেল আপডেট
        video['description'] = request.form.get('description', '')  # ডিসক্রিপশন আপডেট
        save_videos(videos)
        return redirect(url_for('video_admin'))
    
    return render_template('ed_video.html', video=video)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive"})

def keep_alive():
    url = "https://naruto-kun-dailies.onrender.com/ping"  # আপনার ওয়েবসাইটের URL ব্যবহার করুন
    while True:
        time.sleep(300)  # প্রতি ৫ মিনিটে একবার পিং করবে
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("✅ Ping successful")
            else:
                print(f"⚠️ Ping failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    if not os.path.exists(ARTICLES_FILE):
        save_articles([])
    if not os.path.exists(VIDEOS_FILE):
        save_videos([])

    # Keep the app alive in a separate thread
    threading.Thread(target=keep_alive, daemon=True).start()

    app.run(host='0.0.0.0', port=5000)
