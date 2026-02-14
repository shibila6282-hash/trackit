from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import time
import json
import uuid
import logging
from functools import wraps
from dotenv import load_dotenv
from data_manager import (
    load_data, mark_habit_done, skip_habit, add_new_habit,
    get_weekly_data, load_leaderboard, update_leaderboard,
    get_calendar_counts, record_event, add_points, check_rewards,
    load_user_points, calculate_streak, delete_habit, edit_habit
)

# ==================== LOGGING CONFIGURATION ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trackit.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)
logger.info("TrackIt application starting...")

# Load environment variables from .env file
load_dotenv()

# Gemini AI Configuration
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get('TRACKIT_SECRET', 'trackit-dev-secret')

REMINDER_FILE = os.path.join(os.path.dirname(__file__), "reminder.txt")
USERS_FILE = os.path.join(os.path.dirname(__file__), "data", "users.json")

# ==================== AI PERSONA CONFIGURATION ====================
AI_PERSONAS = {
    'motivator': {
        'name': 'Motivator',
        'style': 'energetic and encouraging',
        'tone': 'uses exclamation marks and emojis'
    },
    'coach': {
        'name': 'Coach',
        'style': 'disciplined and strategic',
        'tone': 'focuses on habit science and streaks'
    },
    'friend': {
        'name': 'Friend',
        'style': 'casual and relatable',
        'tone': 'conversational and supportive'
    },
    'mentor': {
        'name': 'Mentor',
        'style': 'wise and reflective',
        'tone': 'offers deep insights and life lessons'
    }
}

def get_user_ai_persona(user_name):
    """Get user's preferred AI persona (default: coach)"""
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f) or {}
        for uid, user_info in users_data.items():
            if user_info.get('name') == user_name:
                persona = user_info.get('ai_persona', 'coach')
                return persona if persona in AI_PERSONAS else 'coach'
    except Exception as e:
        logger.warning(f"Could not retrieve AI persona for {user_name}: {e}")
    return 'coach'  # Default

# ==================== USER ACCOUNT MANAGEMENT ====================
# NOTE: This is a simple session-based system suitable for single-user/small team apps.
# For production/scaling, consider:
# - Move to database (SQLite, PostgreSQL)
# - Implement proper authentication (bcrypt passwords, OAuth, JWT tokens)
# - Add email verification and password reset
# - Use secure cookies with httpOnly, Secure, SameSite flags

def get_or_create_user(user_name):
    """
    Get existing user by name or create new user account with unique ID.
    Returns (user_id, created_bool)
    """
    try:
        if not os.path.exists(USERS_FILE):
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            users_data = {}
        else:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f) or {}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        users_data = {}
    
    # Check if user already exists by name
    for uid, user_info in users_data.items():
        if user_info.get('name') == user_name.strip():
            logger.debug(f"User exists: {user_name}")
            return uid, False  # User exists
    
    # Create new user account
    new_user_id = str(uuid.uuid4())
    users_data[new_user_id] = {
        'name': user_name.strip(),
        'created_at': time.time(),
        'last_login': time.time(),
        'ai_persona': 'coach'  # Default persona
    }
    
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
        logger.info(f"New user account created: {user_name} (ID: {new_user_id})")
    except Exception as e:
        logger.error(f"Error saving user: {e}")
    
    return new_user_id, True  # New user created

def validate_session():
    """
    Validate that session user_id and user_name match.
    Returns True if valid, False otherwise.
    """
    if 'user_id' not in session or 'user_name' not in session:
        return False
    
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f) or {}
        
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        
        # Verify user_id belongs to this user_name
        if users_data.get(user_id, {}).get('name') == user_name:
            return True
    except Exception as e:
        logger.error(f"Session validation error: {e}")
    
    return False

# Rate limiting: track requests per user/identifier
_rate_limit_store = {}
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX_REQUESTS = 10  # max requests per window

def rate_limit(max_requests=5, window=60):
    """Simple rate limiter decorator - limits requests per user/IP per time window"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use user_name if available, otherwise use IP
            identifier = session.get('user_name') or request.remote_addr
            current_time = time.time()
            
            if identifier not in _rate_limit_store:
                _rate_limit_store[identifier] = []
            
            # Clean old requests outside the window
            _rate_limit_store[identifier] = [
                req_time for req_time in _rate_limit_store[identifier]
                if current_time - req_time < window
            ]
            
            # Check if limit exceeded
            if len(_rate_limit_store[identifier]) >= max_requests:
                logger.warning(f"Rate limit exceeded for {identifier}")
                return jsonify({"error": "Rate limit exceeded. Please try again later.", "status": "rate_limited"}), 429
            
            # Record this request
            _rate_limit_store[identifier].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ensure_session_valid():
    """Decorator to validate session before executing route - clears invalid sessions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_name = session.get('user_name', '')
            if user_name and not validate_session():
                logger.warning(f"Invalid session detected - clearing")
                session.clear()
                # Return to index or error page
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_chat_history():
    """Retrieve chat history from session"""
    if 'chat_history' not in session:
        session['chat_history'] = []
    return session['chat_history']

def add_to_chat_history(user_message, ai_reply):
    """Add message pair to chat history"""
    history = get_chat_history()
    history.append({"user": user_message, "ai": ai_reply})
    # Keep last 10 messages to save memory
    if len(history) > 10:
        history = history[-10:]
    session['chat_history'] = history
    session.modified = True

def get_chat_context_summary():
    """Get last few chat messages for AI context"""
    history = get_chat_history()
    if not history:
        return ""
    
    # Format last 3 exchanges for context
    recent = history[-3:] if len(history) >= 3 else history
    context = "Recent conversation context:\n"
    for ex in recent:
        context += f"- User: {ex['user']}\n"
        context += f"- AI: {ex['ai']}\n"
    return context

def get_pending_reward_info(user_name):
    """Check if user has any new rewards and return formatted message"""
    if not user_name or 'reward_msg' not in session:
        return ""
    
    reward_msg = session.pop('reward_msg', '')
    if reward_msg:
        return f"\n\n💝 {reward_msg}"
    return ""

ICON_MAP = {
    'medit': 'meditation.svg', 'medita': 'meditation.svg', 'yoga': 'meditation.svg',
    'run': 'running.svg', 'jog': 'running.svg', 'walk': 'running.svg', 'exercise': 'running.svg',
    'read': 'reading.svg', 'book': 'reading.svg', 'pages': 'reading.svg',
    'water': 'water.svg', 'drink': 'water.svg'
}

def assign_icon(habit_name):
    """Map habit name to icon"""
    name_lower = (habit_name or '').lower()
    return next((v for k, v in ICON_MAP.items() if k in name_lower), 'default.svg')

def is_duplicate_habit(habit_name):
    """Check if a habit already exists in the database"""
    try:
        df = load_data()
        if df.empty:
            return False
        existing_habits = df['habit_name'].tolist()
        return habit_name.lower() in [h.lower() for h in existing_habits]
    except Exception as e:
        logger.error(f"Error checking for duplicate habit: {e}")
        return False

def load_habits_with_rate():
    """Load habits with completion rates and current streak"""
    df = load_data()
    habits = df.to_dict(orient="records")
    for h in habits:
        t = int(h.get("total_days") or 0)
        d = int(h.get("days_completed") or 0)
        h["rate"] = int((d / t) * 100) if t else 0
        h['icon'] = assign_icon(h.get('habit_name'))
        h['streak'] = calculate_streak(h.get('habit_name', ''))
    return habits

def handle_rewards(user_name):
    """Check and handle reward unlocks for a user"""
    if not user_name:
        return
    
    try:
        new_rewards = check_rewards(user_name)
        if new_rewards:
            reward_text = ', '.join(new_rewards)
            session['reward_msg'] = f"Congrats! You unlocked: {reward_text} 🎉"
            logger.info(f"User {user_name} unlocked rewards: {reward_text}")
    except Exception as e:
        logger.error(f"Reward handling error for {user_name}: {e}")

@app.route("/")
def index():
    """Dashboard homepage with habits, points, and rewards"""
    try:
        habits = load_habits_with_rate()
    except Exception as e:
        logger.error(f"Load habits error: {e}")
        habits = []
    
    reminder = ""
    if os.path.exists(REMINDER_FILE):
        with open(REMINDER_FILE, "r") as f:
            reminder = f.read().strip()
    
    user_name = session.get('user_name', '')
    
    # Validate session if user is logged in
    if user_name and not validate_session():
        logger.warning(f"Invalid session detected for user: {user_name}")
        session.clear()
        user_name = ''
    
    overall_rate = int(sum(h.get('rate', 0) for h in habits) / len(habits)) if habits else 0

    # Load points and rewards for user
    points = 0
    rewards = []
    if user_name:
        try:
            update_leaderboard(user_name, overall_rate)
        except Exception as e:
            logger.error(f"Leaderboard update error: {e}")
        
        try:
            user_data = load_user_points().get(user_name, {"points": 0, "rewards": []})
            points = user_data.get("points", 0)
            rewards = user_data.get("rewards", [])
        except Exception as e:
            logger.error(f"Points load error: {e}")

    return render_template("index.html", 
                          habits=habits, 
                          reminder=reminder,
                          user_name=user_name, 
                          overall_rate=overall_rate,
                          points=points, 
                          rewards=rewards)

@app.route("/weekly")
def weekly():
    """Return weekly progress data for chart"""
    try:
        dates, results = get_weekly_data()
        if not dates or not results:
            return jsonify({"success": True, "dates": [], "values": []})
        values = [r[1] for r in results]
        return jsonify({"success": True, "dates": dates, "values": values})
    except Exception as e:
        logger.error(f"Weekly data error: {e}")
        return jsonify({"success": True, "dates": [], "values": []})

@app.route("/leaderboard")
def leaderboard():
    """Return top 10 users on leaderboard"""
    try:
        leaders = load_leaderboard(top_n=10)
        if not leaders:
            return jsonify({"success": True, "top": []})
        return jsonify({"success": True, "top": leaders})
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        return jsonify({"success": True, "top": []})

@app.route("/calendar_data")
def calendar_data():
    """Return calendar completion counts for a given month/year"""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    user = request.args.get('user', default='')
    
    try:
        counts = get_calendar_counts(month=month, year=year, user_name=user if user != 'me' else None)
        if not counts:
            return jsonify({"success": True, "counts": {}, "max": 0})
        max_count = max(counts.values()) if counts else 0
        return jsonify({"success": True, "counts": counts, "max": max_count})
    except Exception as e:
        logger.error(f"Calendar data error: {e}")
        return jsonify({"success": True, "counts": {}, "max": 0})

@app.route("/set_name", methods=["POST"])
def set_user_name():
    """Set user name in session and create/retrieve user account"""
    user_name = request.form.get('user_name', '').strip()
    if user_name:
        # Get or create user account (returns unique user_id)
        user_id, is_new = get_or_create_user(user_name)
        
        # Store both user_id and user_name in session for validation
        session['user_id'] = user_id
        session['user_name'] = user_name
        session.modified = True
        
        if is_new:
            logger.info(f"New user account created: {user_name} (ID: {user_id})")
        else:
            logger.info(f"User logged in: {user_name} (ID: {user_id})")
    
    return redirect(url_for('index'))

@app.route("/add", methods=["POST"])
def add_new_habit_form():
    """Add a new habit"""
    habit_name = request.form.get('name', '').strip()
    if habit_name:
        try:
            # Check for duplicate habits
            if is_duplicate_habit(habit_name):
                logger.warning(f"Duplicate habit attempted: {habit_name}")
                session['error_msg'] = f"Habit '{habit_name}' already exists!"
            else:
                add_new_habit(habit_name)
                logger.info(f"New habit added: {habit_name}")
        except Exception as e:
            logger.error(f"Add habit error: {e}")
            session['error_msg'] = f"Error adding habit: {str(e)}"
    return redirect(url_for('index'))

@app.route("/done", methods=["POST"])
def mark_habit_done_form():
    """Mark a habit as done and award points"""
    habit_name = request.form.get('name', '').strip()
    user_name = session.get('user_name', '')
    
    if habit_name:
        try:
            mark_habit_done(habit_name)
            
            # Record the event for calendar tracking
            if user_name:
                record_event(habit_name, user_name=user_name)
            
            # Award points and check rewards if user logged in
            if user_name:
                points = add_points(user_name, points=10)  # 10 points per habit
                handle_rewards(user_name)
                logger.info(f"User {user_name} earned 10 points (total: {points})")
        except Exception as e:
            logger.error(f"Mark habit done error: {e}")
    
    return redirect(url_for('index'))

@app.route("/skip", methods=["POST"])
def skip_habit_form():
    """Skip a habit without marking it complete"""
    habit_name = request.form.get('name', '').strip()
    if habit_name:
        try:
            skip_habit(habit_name)
            logger.info(f"Habit skipped: {habit_name}")
        except Exception as e:
            logger.error(f"Skip habit error: {e}")
    return redirect(url_for('index'))

@app.route("/delete", methods=["POST"])
def delete_habit_form():
    """Delete a habit"""
    habit_name = request.form.get('name', '').strip()
    if habit_name:
        try:
            if delete_habit(habit_name):
                logger.info(f"User deleted habit: {habit_name}")
                session['success_msg'] = f"Habit '{habit_name}' deleted!"
            else:
                logger.warning(f"Failed to delete habit: {habit_name}")
                session['error_msg'] = f"Error deleting habit"
        except Exception as e:
            logger.error(f"Delete habit error: {e}")
            session['error_msg'] = f"Error deleting habit: {str(e)}"
    return redirect(url_for('index'))

@app.route("/edit", methods=["POST"])
def edit_habit_form():
    """Edit/rename a habit"""
    old_name = request.form.get('old_name', '').strip()
    new_name = request.form.get('new_name', '').strip()
    
    if old_name and new_name:
        try:
            if edit_habit(old_name, new_name):
                logger.info(f"Habit renamed: {old_name} → {new_name}")
                session['success_msg'] = f"Habit renamed to '{new_name}'!"
            else:
                logger.warning(f"Failed to rename habit: {old_name}")
                session['error_msg'] = f"Habit '{new_name}' already exists"
        except Exception as e:
            logger.error(f"Edit habit error: {e}")
            session['error_msg'] = f"Error editing habit: {str(e)}"
    return redirect(url_for('index'))

@app.route("/api/chat", methods=["POST"])
@rate_limit(max_requests=5, window=60)
def chat():
    """Chat endpoint with AI coach - falls back to mock responses"""
    try:
        data = request.json or {}
        user_message = (data.get("message") or "").strip()
        user_name = (session.get('user_name') or 'Friend').strip()
        
        if not user_message:
            return jsonify({"error": "Please enter a message", "status": "error"}), 400
        
        # Get user's habits for context
        try:
            habits = load_habits_with_rate()
        except Exception as e:
            logger.error(f"Load habits error in chat: {e}")
            habits = []
        
        habit_context = "\n".join([f"- {h['habit_name']}: {h['rate']}% complete" for h in habits]) if habits else "No habits yet"
        
        # Get chat history context for longer conversations
        chat_context = get_chat_context_summary()
        
        # Check for pending rewards to mention
        reward_bonus = get_pending_reward_info(user_name)
        
        # Get user's preferred AI persona
        persona_key = get_user_ai_persona(user_name)
        persona = AI_PERSONAS.get(persona_key, AI_PERSONAS['coach'])
        
        # If Gemini is available, use it
        if GEMINI_AVAILABLE:
            try:
                system_prompt = f"""You are TrackIt's habit coach AI called "{persona['name']}". Your communication style is: {persona['style']}
Your role is to:
1. Provide encouragement and motivation
2. Give practical habit improvement tips
3. Celebrate progress and streaks
4. Keep responses short (1-2 sentences max)
5. Be warm, supportive, and non-judgmental
6. Respond in a {persona['tone']} manner

User: {user_name}
Their habits: {habit_context}

{chat_context}"""
                
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(
                    f"{system_prompt}\n\nQuestion: {user_message}",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.8,
                        max_output_tokens=200
                    )
                )
                
                reply = response.text.strip()
                if reply:
                    # Add reward info if available
                    full_reply = reply + reward_bonus if reward_bonus else reply
                    # Store in chat history
                    add_to_chat_history(user_message, full_reply)
                    return jsonify({"reply": full_reply, "status": "success"})
                else:
                    reply_fallback = get_mock_response(user_message, habits, user_name, return_text=True)
                    full_reply = reply_fallback + reward_bonus if reward_bonus else reply_fallback
                    add_to_chat_history(user_message, full_reply)
                    return jsonify({"reply": full_reply, "status": "success"})
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Gemini API error: {error_msg}")
                # Fall back to mock response if API fails
                reply_fallback = get_mock_response(user_message, habits, user_name, return_text=True)
                full_reply = reply_fallback + reward_bonus if reward_bonus else reply_fallback
                add_to_chat_history(user_message, full_reply)
                return jsonify({"reply": full_reply, "status": "success"})
        else:
            # No API key - use mock response
            reply_fallback = get_mock_response(user_message, habits, user_name, return_text=True)
            full_reply = reply_fallback + reward_bonus if reward_bonus else reply_fallback
            add_to_chat_history(user_message, full_reply)
            return jsonify({"reply": full_reply, "status": "success"})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Chat error: {error_msg}")
        return jsonify({"error": "Assistant error", "status": "error"}), 500

def get_mock_response(user_message, habits, user_name, return_text=False):
    """Provide mock AI responses when API is not configured"""
    msg_lower = user_message.lower()
    
    # Select response based on message
    if any(word in msg_lower for word in ['improve', 'better', 'tips', 'help', 'advice']):
        reply = "Great question! Pick your hardest habit and focus on 3 days in a row. Once you break through, momentum builds itself! 💪"
    elif any(word in msg_lower for word in ['motivation', 'motivate', 'inspire', 'encourage']):
        reply = "You're already here tracking your habits - that's the hardest part! Every single day counts. Keep crushing it! 🌿✨"
    elif any(word in msg_lower for word in ['streak', 'progress', 'doing', 'how']):
        if habits:
            top_habit = max(habits, key=lambda h: h.get('rate', 0))
            reply = f"Your '{top_habit['habit_name']}' is at {top_habit['rate']}%! Keep that momentum! 🔥"
        else:
            reply = "You're building something amazing. Every day counts! 🎯"
    elif any(word in msg_lower for word in ['slack', 'skip', 'break', 'hard', 'difficult', 'struggle']):
        reply = "I hear you! Even the best habit trackers take breaks. What matters is getting back on track tomorrow. You've got this! 💙"
    else:
        # Generic encouraging response
        reply = "That's a great question! Remember: consistency over perfection. Every small win counts! 🌱"
    
    if return_text:
        return reply
    else:
        return jsonify({"reply": reply, "status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
