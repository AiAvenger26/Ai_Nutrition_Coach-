from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import base64
import io
from datetime import date, datetime
from pymongo import MongoClient
from bson import ObjectId
import gridfs

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

client_openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
mongo_client = MongoClient(mongo_uri)
db = mongo_client['nutrition_coach']
users = db['users']
food_logs = db['food_logs']
fs = gridfs.GridFS(db)

NUTRITION_DB = {
    'pizza': {'calories': 266, 'protein': 11, 'carbs': 33, 'fats': 10},
    'apple': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fats': 0.2},
    'banana': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fats': 0.3},
    'chicken': {'calories': 239, 'protein': 27, 'carbs': 0, 'fats': 14},
    'salad': {'calories': 15, 'protein': 1, 'carbs': 3, 'fats': 0.2},
    'burger': {'calories': 254, 'protein': 12, 'carbs': 26, 'fats': 12},
    'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fats': 0.3},
    'bread': {'calories': 265, 'protein': 9, 'carbs': 49, 'fats': 3.2},
}

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        user = users.find_one({'$or': [{'username': username}, {'email': email}]})
        if user:
            flash('Username or email already exists.')
            return render_template('register.html')
        
        users.insert_one({
            'username': username,
            'email': email,
            'password': password,
            'age': 0,
            'height': 0,
            'weight': 0,
            'bmi': 0
        })
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    today = date.today().isoformat()
    
    foods = list(food_logs.find({
        'user_id': user_id,
        'log_date': today
    }).sort('created_at', -1))
    
    user = users.find_one({'_id': ObjectId(user_id)})
    
    return render_template('dashboard.html', foods=foods, today=today, user=user)

@app.route('/add_food', methods=['POST'])
def add_food():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_id = session['user_id']
    today = date.today().isoformat()
    
    result = food_logs.insert_one({
        'user_id': user_id,
        'food_name': data['food_name'],
        'calories': data['calories'],
        'protein': data['protein'],
        'carbs': data['carbs'],
        'fats': data['fats'],
        'log_date': today,
        'created_at': datetime.utcnow()
    })
    
    return jsonify({'success': True, 'id': str(result.inserted_id)})

@app.route('/food_logs')
@app.route('/get_foods')
def get_food_logs():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    today = date.today().isoformat()
    
    logs = list(food_logs.find({
        'user_id': user_id,
        'log_date': today
    }).sort('created_at', -1))
    
    log_list = [{'id': str(l['_id']), 'food_name': l['food_name'], 'calories': l['calories'],
                 'protein': l['protein'], 'carbs': l['carbs'], 'fats': l['fats']} for l in logs]
    
    return jsonify({'logs': log_list})

@app.route('/delete_food/<food_id>', methods=['DELETE'])
def delete_food(food_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    result = food_logs.delete_one({'_id': ObjectId(food_id), 'user_id': user_id})
    
    return jsonify({'success': result.deleted_count > 0})

@app.route('/detect-food-ai', methods=['POST'])
def detect_food_ai():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not client_openai.api_key:
        return jsonify({'error': 'OpenAI API key not configured'}), 500
    
    image_b64 = request.json['image_base64'].split(',')[1]
    
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify the main food item. Return ONLY food name lowercase."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ],
            max_tokens=20
        )
        
        food_name = response.choices[0].message.content.strip().lower()
        nutrition = NUTRITION_DB.get(food_name, {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0})
        
        return jsonify({'food_name': food_name, 'nutrition': nutrition, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/analyze-body', methods=['POST'])
def analyze_body():
    image_b64 = request.json['image_base64'].split(',')[1]
    
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze body type (lean/athletic/average/overweight/obese). Give 3 meal suggestions. Format: TYPE\\n• Suggestion 1"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ]
        )
        
        return jsonify({'analysis': response.choices[0].message.content, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/calculate-bmi', methods=['POST'])
def calculate_bmi():
    data = request.json
    height_m = float(data['height']) / 100
    weight = float(data['weight'])
    
    bmi = weight / (height_m ** 2)
    
    category = 'Normal'
    if bmi < 18.5:
        category = 'Underweight'
    elif bmi >= 25 and bmi < 30:
        category = 'Overweight'
    elif bmi >= 30:
        category = 'Obese'
    
    return jsonify({
        'bmi': round(bmi, 1),
        'category': category,
        'health': f'BMI {bmi:.1f} ({category})'
    })

@app.route('/ai_recommendations')
def ai_recommendations():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    today = date.today().isoformat()
    
    pipeline = [
        {'$match': {'user_id': user_id, 'log_date': today}},
        {'$group': {'_id': None, 'calories': {'$sum': '$calories'}, 'protein': {'$sum': '$protein'}}}
    ]
    
    result = list(food_logs.aggregate(pipeline))
    totals = result[0] if result else {'calories': 0, 'protein': 0}
    
    suggestions = []
    if totals['calories'] > 2500:
        suggestions.append("High calories - lighter dinner recommended")
    if totals['protein'] < 50:
        suggestions.append("Low protein - add chicken or eggs")
    else:
        suggestions.append("Great balance today!")
    
    return jsonify({'suggestions': suggestions, 'totals': totals})

@app.route('/weekly_data')
def weekly_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    from datetime import timedelta
    
    days = []
    calories = []
    for i in range(7):
        d = (date.today() - timedelta(days=i)).isoformat()
        foods = list(food_logs.find({'user_id': user_id, 'log_date': d}))
        days.append(d)
        calories.append(sum(f['calories'] for f in foods))
    
    return jsonify({'days': days[::-1], 'calories': calories[::-1]})

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = ObjectId(session['user_id'])
    
    if request.method == 'POST':
        data = request.json
        users.update_one(
            {'_id': user_id},
            {'$set': {
                'age': int(data['age']),
                'height': float(data['height']),
                'weight': float(data['weight'])
            }}
        )
        return jsonify({'success': True})
    
    user = users.find_one({'_id': user_id})
    return jsonify({
        'age': user.get('age', 0),
        'height': user.get('height', 0),
        'weight': user.get('weight', 0),
        'bmi': user.get('bmi', 0)
    })

@app.route('/nutrition')
def nutrition():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    today = date.today().isoformat()
    
    pipeline = [
        {'$match': {'user_id': user_id, 'log_date': today}},
        {'$group': {
            '_id': None,
            'energy': {'$sum': '$calories'},
            'protein': {'$sum': '$protein'},
            'carbs': {'$sum': '$carbs'},
            'fat': {'$sum': '$fats'}
        }}
    ]
    
    result = list(food_logs.aggregate(pipeline))
    totals = result[0] if result else {'energy': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    
    return jsonify(totals)

@app.route('/ai-advice', methods=['POST'])
def ai_advice():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not client_openai.api_key:
        return jsonify({'error': 'OpenAI API not configured'}), 500
    
    user_id = session['user_id']
    today = date.today().isoformat()
    
    # Get profile and today's totals
    user = users.find_one({'_id': ObjectId(user_id)})
    pipeline = [
        {'$match': {'user_id': user_id, 'log_date': today}},
        {'$group': {
            '_id': None,
            'protein': {'$sum': '$protein'},
            'calories': {'$sum': '$calories'}
        }}
    ]
    stats = list(food_logs.aggregate(pipeline))
    totals = stats[0] if stats else {'protein': 0, 'calories': 0}
    
    prompt = f"""
    You are nutrition coach. User profile: age {user.get('age', 0)}, BMI {user.get('bmi', 0):.1f}
    Today: {totals['calories']} cal, {totals['protein']}g protein
    Give 3 short actionable tips.
    """
    
    response = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return jsonify({'advice': response.choices[0].message.content})

if __name__ == '__main__':
    users.create_index('username')
    food_logs.create_index('user_id')
    food_logs.create_index('log_date')
    app.run(debug=True, port=5000)

