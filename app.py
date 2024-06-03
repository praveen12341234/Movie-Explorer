import os
from flask import Flask, render_template, request, redirect, session, flash, url_for
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Initialize Firebase Admin SDK using the JSON credentials from the environment variable
firebase_key_json = os.getenv('FIREBASE_KEY_JSON')
firebase_key_dict = json.loads(firebase_key_json)
cred = credentials.Certificate(firebase_key_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

OMDB_API_KEY = 'f2377158'

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_email' in session:
        user_email = session['user_email']
        playlists_ref = db.collection('playlists').document(user_email)
        playlists_doc = playlists_ref.get()
        playlists = playlists_doc.to_dict() if playlists_doc.exists else {}

        if request.method == 'POST':
            movie_name = request.form['movie_name']
            return search_movie(movie_name, playlists)

        return render_template('index.html', playlists=playlists)
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.get_user_by_email(email)
            session['user_email'] = email
            return redirect('/')
        except Exception as e:
            flash('Authentication failed: {}'.format(str(e)), 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.create_user(email=email, password=password)
            flash('Account created successfully. Please log in with your credentials.', 'success')
            return redirect('/login')
        except Exception as e:
            flash('Failed to create account: {}'.format(str(e)), 'error')
            return redirect('/signup')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/login')

def search_movie(movie_name, playlists):
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"

    response = requests.get(url)
    if response.status_code == 200:
        movie_details = response.json()
        if movie_details.get('Response') == 'True':
            return render_template('result.html', movie_name=movie_name, movie_details=movie_details, playlists=playlists)
        else:
            flash(f"Movie '{movie_name}' not found.", 'error')
            return render_template('result.html', movie_name=movie_name, movie_details=None, playlists=playlists)
    else:
        flash("Failed to fetch movie details. Please try again later.", 'error')
        return render_template('result.html', movie_name=movie_name, movie_details=None, playlists=playlists)

@app.route('/add_to_playlist_form/<movie_name>', methods=['GET'])
def add_to_playlist_form(movie_name):
    if 'user_email' not in session:
        return redirect('/login')

    user_email = session['user_email']
    playlists_ref = db.collection('playlists').document(user_email)
    playlists_doc = playlists_ref.get()
    playlists = playlists_doc.to_dict() if playlists_doc.exists else {}

    return render_template('add_to_playlist.html', movie_name=movie_name, playlists=playlists)

@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    if 'user_email' not in session:
        return redirect('/login')

    user_email = session['user_email']
    movie_name = request.form['movie_name']
    selected_playlists = request.form.getlist('selected_playlists')
    new_playlist_name = request.form.get('new_playlist_title')
    access_type = request.form.get('new_playlist_access', 'private')

    playlists_ref = db.collection('playlists').document(user_email)
    playlists_doc = playlists_ref.get()
    playlists = playlists_doc.to_dict() if playlists_doc.exists else {}

    if new_playlist_name:
        if new_playlist_name not in playlists:
            playlists[new_playlist_name] = {'movies': [], 'access': access_type}
        if movie_name not in playlists[new_playlist_name]['movies']:
            playlists[new_playlist_name]['movies'].append(movie_name)

    for playlist_name in selected_playlists:
        if playlist_name in playlists:
            if movie_name not in playlists[playlist_name]['movies']:
                playlists[playlist_name]['movies'].append(movie_name)

    playlists_ref.set(playlists)
    flash(f'Movie "{movie_name}" added to selected playlists.', 'success')

    return redirect('/')

@app.route('/view_playlist/<playlist_name>', methods=['GET'])
def view_playlist(playlist_name):
    user_email = session.get('user_email')
    referrer = request.referrer

    playlists_ref = db.collection('playlists')
    all_playlists_docs = playlists_ref.stream()
    found_playlist = False

    for doc in all_playlists_docs:
        playlists = doc.to_dict()
        if playlist_name in playlists:
            found_playlist = True
            playlist_owner_email = doc.id
            playlist = playlists[playlist_name]['movies']
            access_type = playlists[playlist_name].get('access', 'private')
            break

    if not found_playlist:
        return "Playlist not found", 404

    if playlist_owner_email == user_email or access_type == 'public':
        return render_template('view_playlist.html', playlist_name=playlist_name, playlist=playlist, access_type=access_type, owner=playlist_owner_email == user_email)
    else:
        if referrer and url_for('index', _external=True) in referrer:
            return render_template('view_playlist.html', playlist_name=playlist_name, playlist=playlist, access_type=access_type, owner=playlist_owner_email == user_email)
        else:
            return render_template('access_denied.html')

@app.route('/copy_url/<playlist_name>', methods=['POST'])
def copy_url(playlist_name):
    user_email = session.get('user_email')
    playlists_ref = db.collection('playlists').document(user_email)
    playlists_doc = playlists_ref.get()
    playlists = playlists_doc.to_dict() if playlists_doc.exists else {}

    access_type = playlists[playlist_name]['access'] if playlist_name in playlists else 'private'

    if access_type == 'private':
        playlist_url = url_for('access_denied', _external=True)
    else:
        playlist_url = url_for('view_playlist', playlist_name=playlist_name, _external=True)

    return playlist_url

@app.route('/access_denied')
def access_denied():
    return render_template('access_denied.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
