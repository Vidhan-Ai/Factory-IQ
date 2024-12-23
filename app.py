from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from PIL import Image
from flask_migrate import Migrate
from functools import wraps
from dotenv import load_dotenv
import os
import h2o
import pandas as pd
import numpy as np
from h2o.automl import H2OAutoML
import plotly.express as px
import plotly.io as pio
import requests

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)


data = {
    'date': pd.date_range(start='2024-01-01', periods=12, freq='ME'),
    'sales': [120, 150, 180, 210, 240, 260, 220, 190, 170, 200, 230, 250],
    'categories': ['Electronics', 'Clothing', 'Furniture', 'Electronics', 'Clothing', 'Furniture', 'Electronics', 'Clothing', 'Furniture', 'Electronics', 'Clothing', 'Furniture'],
    'regions': ['North', 'South', 'East', 'West', 'North', 'South', 'East', 'West', 'North', 'South', 'East', 'West'],
    'complaints': ['delivery', 'price', 'quality', 'availability', 'return', 'service', 'return', 'price', 'quality', 'service', 'availability', 'delivery']
}

df = pd.DataFrame(data)


@app.route('/get_weather', methods=['POST'])
def get_weather():
    data = request.json
    lat = data['latitude']
    lon = data['longitude']

    # Fetch weather data from OpenWeatherMap API
    WEATHER_API_KEY = os.getenv('API_KEY')
    url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric'
    response = requests.get(url)
    weather_data = response.json()

    if response.status_code == 200:
        return jsonify({'location': weather_data['name'],
        'temperature': weather_data['main']['temp'],
        'description': weather_data['weather'][0]['description'],
        'icon': weather_data['weather'][0]['icon']})
    else :
        return jsonify({'error':'Unable to fetch weather data'}), 500


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    profile = db.Column(db.String(150)) 

facebook_bp = make_facebook_blueprint(
    client_id=os.getenv('FACEBOOK_CLIENT_ID'),
    client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
    redirect_to='facebook_login'
)
app.register_blueprint(facebook_bp, url_prefix="/facebook_login")

google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    redirect_to='google_login'
)

app.register_blueprint(google_bp, url_prefix="/google_login")

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@app.route('/facebook_login')
def facebook_login():
    if not facebook.authorized:
        return redirect(url_for('facebook.login'))
    resp = facebook.get("/me?fields=id,name,email")
    assert resp.ok, resp.text
    user_info = resp.json()
    return f"Welcome {user_info['name']}!"

@app.route('/google_login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    user_info = resp.json()
    
    profile = user_info['picture']
    username = user_info['name']
    
    session['username'] = username
    session['profile'] = profile
    
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        
        if user:
            if bcrypt.check_password_hash(user.password, password):
                session['name'] = user.name
                session['username'] = user.username 
                session['profile'] = user.profile  
                return '''
                    <script>
                        alert('Login successful!');
                        window.location.href = '{}';
                    </script>
                '''.format(url_for('index'))  
            else:
                return '''
                    <script>
                        alert('Login failed. Incorrect password.');
                        window.location.href = '{}';
                    </script>
                '''.format(url_for('login'))
        else:
            return '''
                <script>
                    alert('Login failed. Username not found.');
                    window.location.href = '{}';
                </script>
            '''.format(url_for('login'))
        
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    return login()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['Firstn']
        last_name = request.form['Lastn']
        full_name = f"{first_name} {last_name}"

        username = request.form['username']
        password = request.form['password']

        if 'profile' not in request.files:
            return '''
                <script>
                    alert('No file.');
                    window.location.href = '{}';
                </script>
            '''.format(url_for('signup'))

        file = request.files['profile']

        if file.filename == '':
            return '''
                <script>
                    alert('No file selected.');
                    window.location.href = '{}';
                </script>
            '''.format(url_for('signup'))

        if file and allowed_file(file.filename):
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{username}.{file_extension}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(img_path)

            with Image.open(img_path) as img:
                img = img.resize((40, 40), Image.LANCZOS)
                img.save(img_path)

            if User.query.filter_by(username=username).first():
                return '''
                    <script>
                        alert('User already exists.');
                        window.location.href = '{}';
                    </script>
                '''.format(url_for('signup'))

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=hashed_password, profile=filename, name=full_name) 

            db.session.add(new_user)
            db.session.commit()

            return '''
            <script>
                alert('Signup successful!');
                window.location.href = '{}';
            </script>
            '''.format(url_for('login'))

        else:
            return '''
                <script>
                    alert('Invalid file type.');
                    window.location.href = '{}';
                </script>
            '''.format(url_for('signup'))

    return render_template('signup.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/index')
@login_required
@nocache
def index():
    if 'username' in session: 
        profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
        return render_template('index.html', profile=profile_url)   
    else:
        return '''
            <script>
                alert('Please log in first.');
                window.location.href = '{}';
            </script>
        '''.format(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Monthly/Seasonal Demand API
@app.route('/api/demand-trend', methods=['GET'])
def demand_trend():
    fig = px.line(df, x='date', y='sales', width=500)
    fig.update_layout(
        font_family="Courier New",
        font_color="white",
        legend_title_font_color="green",
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor='rgba(255, 255, 255, 0.2)'
    )
    graph_json = fig.to_json()
    return jsonify(graph_json)

# Product Categories Purchased API
@app.route('/api/product-categories', methods=['GET'])
def product_categories():
    fig = px.bar(df, x='categories', y='sales', width=500)
    fig.update_layout(
        font_family="Courier New",
        font_color="white",
        legend_title_font_color="green",
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor='rgba(255, 255, 255, 0.2)'
    )
    graph_json = fig.to_json()
    return jsonify(graph_json)

# Customer Complaints API (Word Cloud or Bar Chart)
@app.route('/api/customer-complaints', methods=['GET'])
def customer_complaints():
    complaints_count = df['complaints'].value_counts().reset_index()
    complaints_count.columns = ['complaint', 'count']
    fig = px.bar(complaints_count, x='complaint', y='count', width=500)
    fig.update_layout(
        font_family="Courier New",
        font_color="white",
        legend_title_font_color="green",
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor='rgba(255, 255, 255, 0.2)'
    )
    graph_json = fig.to_json()
    return jsonify(graph_json)

# Feedback Trends API
@app.route('/api/feedback-trends', methods=['GET'])
def feedback_trends():
    fig = px.line(df, x='date', y='sales', width=500)  # Example data
    fig.update_layout(
        font_family="Courier New",
        font_color="white",
        legend_title_font_color="green",
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor='rgba(255, 255, 255, 0.2)'
    )
    graph_json = fig.to_json()
    return jsonify(graph_json)

# Top Selling Products API
@app.route('/api/top-selling-products', methods=['GET'])
def top_selling_products():
    top_products = df.groupby('categories')['sales'].sum().reset_index()
    fig = px.bar(top_products, x='categories', y='sales', width=500)
    fig.update_layout(
        font_family="Courier New",
        font_color="white",
        legend_title_font_color="green",
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor='rgba(255, 255, 255, 0.2)'
    )
    graph_json = fig.to_json()
    return jsonify(graph_json)

# Product Sales by Region API
@app.route('/api/sales-by-region', methods=['GET'])
def sales_by_region():
    sales_by_region = df.groupby('regions')['sales'].sum().reset_index()
    fig = px.pie(sales_by_region, names='regions', values='sales', width=500)
    fig.update_layout(
        font_family="Courier New",
        font_color="white",
        legend_title_font_color="green",
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor='rgba(255, 255, 255, 0.2)'
    )
    graph_json = fig.to_json()
    return jsonify(graph_json)

# Product Return Rate API (Dummy data used here for demonstration)
@app.route('/api/return-rate', methods=['GET'])
def return_rate():
    return_rate_data = {
        'Product': ['Electronics', 'Clothing', 'Furniture'],
        'ReturnRate': [5, 10, 15]
    }
    return_df = pd.DataFrame(return_rate_data)
    fig = px.bar(return_df, x='Product', y='ReturnRate', width=500)
    fig.update_layout(
        font_family="Courier New",
        font_color="white",
        legend_title_font_color="green",
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor='rgba(255, 255, 255, 0.2)'
    )
    graph_json = fig.to_json()
    return jsonify(graph_json)

@app.route('/privacy')
@login_required
def privacy():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('privacy.html',profile = profile_url)

@app.route('/terms')
@login_required
def terms():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('terms.html',profile = profile_url)

@app.route('/about')
@login_required
def about():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('about.html',profile = profile_url)

@app.route('/customer')
@login_required
def customer():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('customer-insight.html',profile = profile_url)


@app.route('/faq')
@login_required
def faq():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('faq.html',profile = profile_url)

@app.route('/profile')
@login_required
@nocache
def profile():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('faq.html',profile = profile_url)

@app.route('/supply')
@login_required
def supply():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('supply.html',profile = profile_url)

@app.route('/production')
@login_required
def production():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('production.html',profile = profile_url)

@app.route('/settings')
@login_required
def settings():
    profile_url = url_for('uploaded_file', filename=session.get('profile')) if session.get('profile') else None
    return render_template('settings.html',profile = profile_url)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
