from flask import Flask, jsonify, request
try:
    from .data_manager import load_data, mark_habit_done, skip_habit, add_new_habit, get_weekly_data
except Exception:
    from data_manager import load_data, mark_habit_done, skip_habit, add_new_habit, get_weekly_data
import os, datetime, random
import threading, time

REMINDER_FILE = os.path.join(os.path.dirname(__file__), "reminder.txt")

# Reward system
REWARD_CATEGORIES = {
    'exercise': ['Take a 10-min break 🧘', 'Grab a protein snack 🥗', 'Get a cold drink 💧', 'Stretch it out 🤸'],
    'read': ['Listen to 15 min of music 🎵', 'Treat yourself to a latte ☕', 'Short scroll break 📱', 'Cozy rest time 🛋️'],
    'medita': ['Treat yourself to a cup of tea 🍵', 'Take a calming walk 🚶', 'Listen to your fave song 🎶', 'Journal your thoughts ✍️'],
    'yoga': ['Enjoy a warm bath 🛁', 'Treat yourself to a snack 🍪', 'Read something inspiring 📚', 'Relax for 15 min 😌'],
    'water': ['Treat yourself to a fruit smoothie 🍓', 'Enjoy a healthy snack 🥕', 'Pat yourself on the back 👏', 'Hydration win! 💧'],
    'sleep': ['Sleep in 15 min extra tomorrow 🌙', 'Enjoy a cozy evening 🕯️', 'No rush morning tomorrow ⏰', 'Dream sweet dreams ✨'],
    'work': ['Take a power break 💪', 'Celebrate with a treat 🍰', 'Relax for 20 min 😎', 'Reward yourself with your hobby 🎨'],
    'learn': ['Share what you learned! 🗣️', 'Treat yourself to a snack 🍫', 'Take a learning break 📖', 'Celebrate your progress! 🎉'],
}

WEEKLY_REWARDS = [
    '7-day streak! Treat yourself to your favorite meal 🍕',
    'Week crushed! Get yourself something nice 🎁',
    'Consistency king/queen! Movie night marathon 🎬',
    'First week wins! You deserve a rest day 😌',
    'Habit hero! Small shopping spree incoming 🛍️',
]

MONTHLY_REWARDS = [
    'A full month of wins! Plan that trip you wanted ✈️',
    'Monthly champion! Time for a spa day 💆',
    'Whole month crushed! Video game marathon 🎮',
    '30 days of greatness! Invest in yourself 📚',
    'Monthly legend! Skip a chore and relax 🏖️',
]

def get_reward(habit_name):
    """Get a personalized reward based on habit"""
    habit_lower = (habit_name or '').lower()
    for category, rewards in REWARD_CATEGORIES.items():
        if category in habit_lower:
            return random.choice(rewards)
    # Default rewards if no category match
    default_rewards = [
        'You earned a 10-min break! ☕',
        'Treat yourself to a snack 🍪',
        'Take a victory walk 🚶',
        'You deserve some downtime 😎',
    ]
    return random.choice(default_rewards)

def get_reminder_time():
    if os.path.exists(REMINDER_FILE):
        with open(REMINDER_FILE, "r") as f:
            t = f.read().strip()
            if t:
                h, m = map(int, t.split(":"))
                return h, m
    return 20, 0  # default 8 PM

def reminder_loop():
    from plyer import notification
    while True:
        h, m = get_reminder_time()
        now = datetime.datetime.now()
        target = now.replace(hour=h, minute=m, second=0)
        wait = (target - now).total_seconds()
        if wait < 0:
            wait += 86400
        time.sleep(wait)
        notification.notify(
            title="TrackIt Reminder 🌿",
            message="Hey user! Time to update your habits!",
            timeout=10
        )


# Flask API handlers
def create_gui_routes(app):
    """Register Flask routes for habit tracking UI"""
    
    @app.route("/api/mark-done/<habit_name>", methods=["POST"])
    def mark_done(habit_name):
        msg = mark_habit_done(habit_name)
        quotes = [
            "Keep going, you're doing amazing! 💪",
            "Small steps lead to big change 🌱",
            "Every habit counts — stay consistent 🌿",
            "Progress, not perfection! 🌸",
            "You're building a better you! ✨"
        ]
        motivation = random.choice(quotes)
        reward = get_reward(habit_name)
        return jsonify({
            "status": "success", 
            "message": msg, 
            "motivation": motivation,
            "reward": reward
        })

    @app.route("/api/skip-day/<habit_name>", methods=["POST"])
    def skip_day(habit_name):
        msg = skip_habit(habit_name)
        return jsonify({"status": "success", "message": msg})

    @app.route("/api/add-habit", methods=["POST"])
    def add_habit():
        data = request.json
        habit_name = data.get("habit_name", "").strip()
        if not habit_name:
            return jsonify({"status": "error", "message": "Please enter a habit name!"}), 400
        msg = add_new_habit(habit_name)
        return jsonify({"status": "success", "message": msg})

    @app.route("/api/set-reminder", methods=["POST"])
    def set_reminder():
        data = request.json
        time_str = data.get("time", "").strip()
        try:
            h, m = map(int, time_str.split(":"))
            if 0 <= h < 24 and 0 <= m < 60:
                with open(REMINDER_FILE, "w") as f:
                    f.write(time_str)
                return jsonify({"status": "success", "message": f"Reminder set for {time_str}"})
            else:
                return jsonify({"status": "error", "message": "Please enter valid time (00:00–23:59)"}), 400
        except:
            return jsonify({"status": "error", "message": "Invalid format! Example: 20:30"}), 400

    @app.route("/api/weekly-reward", methods=["GET"])
    def weekly_reward():
        """Get a reward suggestion for 7-day streak"""
        reward = random.choice(WEEKLY_REWARDS)
        return jsonify({"status": "success", "reward": reward})

    @app.route("/api/monthly-reward", methods=["GET"])
    def monthly_reward():
        """Get a reward suggestion for 30-day streak"""
        reward = random.choice(MONTHLY_REWARDS)
        return jsonify({"status": "success", "reward": reward})

def run_app():
    """Start the reminder background thread"""
    threading.Thread(target=reminder_loop, daemon=True).start()

if __name__ == "__main__":
    # For testing, the Flask app from app.py should be used instead
    from app import app
    create_gui_routes(app)
    threading.Thread(target=reminder_loop, daemon=True).start()
    app.run(debug=True)
