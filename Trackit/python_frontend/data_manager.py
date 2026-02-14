import pandas as pd
import os
import json
import logging
from datetime import date, datetime, timedelta

# Configure logger
logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "habits.csv")
POINTS_FILE = os.path.join(os.path.dirname(__file__), "data", "points.json")
LEADERBOARD_PATH = os.path.join(os.path.dirname(__file__), "data", "leaderboard.csv")
EVENTS_PATH = os.path.join(os.path.dirname(__file__), "data", "events.csv")

def load_data():
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=["habit_name", "days_completed", "total_days", "last_date"])
        df.to_csv(DATA_PATH, index=False)
    df = pd.read_csv(DATA_PATH)
    if "last_date" not in df.columns:
        df["last_date"] = ""
    return df

def save_data(df):
    df.to_csv(DATA_PATH, index=False)

def mark_habit_done(habit_name):
    df = load_data()
    # normalize dtypes to avoid assignment errors when CSV had empty/NaN columns
    if "last_date" in df.columns:
        df["last_date"] = df["last_date"].fillna("").astype(str)
    else:
        df["last_date"] = ""
    df["days_completed"] = df["days_completed"].fillna(0).astype(int)
    df["total_days"] = df["total_days"].fillna(0).astype(int)
    today = str(date.today())

    for i, row in df.iterrows():
        if row["habit_name"] == habit_name:
            if str(row["last_date"]) != today:
                df.at[i, "days_completed"] += 1
                df.at[i, "total_days"] += 1
                df.at[i, "last_date"] = today
            else:
                return "Already marked today ✅"
            break
    save_data(df)
    return "Updated successfully ✅"

def skip_habit(habit_name):
    df = load_data()
    df["total_days"] = df["total_days"].fillna(0).astype(int)
    df["last_date"] = df["last_date"].fillna("").astype(str)
    for i, row in df.iterrows():
        if row["habit_name"] == habit_name:
            df.at[i, "total_days"] = int(df.at[i, "total_days"]) + 1
            break
    save_data(df)
    return "Skipped ❌"

def delete_habit(habit_name):
    """Delete a habit from the database"""
    try:
        df = load_data()
        df = df[df["habit_name"] != habit_name]
        save_data(df)
        logger.info(f"Habit deleted: {habit_name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting habit {habit_name}: {e}")
        return False

def edit_habit(old_name, new_name):
    """Rename a habit in the database"""
    try:
        df = load_data()
        # Check if new name already exists
        if new_name in df["habit_name"].values and new_name != old_name:
            logger.warning(f"Cannot rename: habit '{new_name}' already exists")
            return False
        
        # Rename the habit
        df.loc[df["habit_name"] == old_name, "habit_name"] = new_name
        save_data(df)
        logger.info(f"Habit renamed: {old_name} → {new_name}")
        return True
    except Exception as e:
        logger.error(f"Error renaming habit {old_name}: {e}")
        return False

def add_new_habit(habit_name):
    df = load_data()
    if habit_name in list(df["habit_name"]):
        return "Habit already exists!"
    new_row = {"habit_name": habit_name, "days_completed": 0, "total_days": 0, "last_date": ""}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    return f"Habit '{habit_name}' added successfully!"


def get_weekly_data():
    """Return 7-day history of completion rates"""
    df = load_data()
    today = datetime.today()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    results = []
    for day in dates:
        total = int(df["total_days"].sum() or 0)
        done = int(df["days_completed"].sum() or 0)
        rate = 0 if total == 0 else round((done / total) * 100, 1)
        results.append((day, rate))
    return dates, results

def load_user_points():
    """Load user points from JSON file"""
    try:
        if not os.path.exists(POINTS_FILE):
            return {}
        with open(POINTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading points: {e}")
        return {}

def save_user_points(points_data):
    """Save user points to JSON file"""
    try:
        os.makedirs(os.path.dirname(POINTS_FILE), exist_ok=True)
        with open(POINTS_FILE, "w") as f:
            json.dump(points_data, f, indent=2)
    except IOError as e:
        logger.error(f"Error saving points: {e}")

def add_points(user_name, points=10):
    """Add points to user and return total"""
    data = load_user_points()
    if user_name not in data:
        data[user_name] = {"points": 0, "rewards": []}
    current_points = int(data[user_name].get("points", 0))
    data[user_name]["points"] = current_points + int(points)
    data[user_name]["last_point_earned"] = datetime.now().isoformat()  # Timestamp
    save_user_points(data)
    return data[user_name]["points"]

def check_rewards(user_name):
    """Return new rewards if milestones reached. Rewards now include earned_at timestamp."""
    milestones = {50: "Bronze Badge 🥉", 100: "Silver Badge 🥈", 200: "Gold Badge 🥇"}
    data = load_user_points()
    user_data = data.get(user_name, {"points": 0, "rewards": []})
    new_rewards = []
    current_points = int(user_data.get("points", 0))
    
    # Normalize existing rewards to handle both string and dict formats
    existing_rewards = user_data.get("rewards", [])
    reward_names = [r if isinstance(r, str) else r.get("name", "") for r in existing_rewards]
    
    for points, reward_name in milestones.items():
        if current_points >= points and reward_name not in reward_names:
            reward_obj = {
                "name": reward_name,
                "earned_at": datetime.now().isoformat(),
                "points_at_earn": current_points
            }
            user_data["rewards"].append(reward_obj)
            new_rewards.append(reward_name)
            logger.info(f"User {user_name} earned reward: {reward_name} at {current_points} points")
    
    if new_rewards:
        data[user_name] = user_data
        save_user_points(data)
    
    return new_rewards

def calculate_streak(habit_name):
    """Calculate current streak (consecutive days) for a habit"""
    try:
        _ensure_events()
        df = pd.read_csv(EVENTS_PATH)
        if df.empty:
            return 0
        
        # Filter for this habit
        filt = df[df["habit_name"] == habit_name].copy()
        if filt.empty:
            return 0
        
        # Convert to datetime and sort
        filt["date"] = pd.to_datetime(filt["date"], errors="coerce")
        filt = filt.dropna(subset=["date"])
        if filt.empty:
            return 0
        
        filt = filt.sort_values("date", ascending=False)
        dates = filt["date"].dt.date.unique()
        
        # Calculate streak from today backwards
        today = date.today()
        streak = 0
        current_date = today
        
        for d in dates:
            if d == current_date or d == current_date - timedelta(days=1):
                streak += 1
                current_date = d
            else:
                break
        
        return streak
    except Exception as e:
        logger.error(f"Error calculating streak for {habit_name}: {e}")
        return 0

# --- Completion events logging for calendar / history ---

def _ensure_events():
    """Create events file if it doesn't exist"""
    try:
        os.makedirs(os.path.dirname(EVENTS_PATH), exist_ok=True)
        if not os.path.exists(EVENTS_PATH):
            edf = pd.DataFrame(columns=["date", "habit_name", "user_name"])
            edf.to_csv(EVENTS_PATH, index=False)
    except IOError as e:
        logger.error(f"Error ensuring events file: {e}")

def record_event(habit_name, when=None, user_name=None):
    """Append a completion event for habit_name on date `when` (YYYY-MM-DD or date obj).
    Optionally associate the event with `user_name`.
    """
    try:
        _ensure_events()
        if when is None:
            when = date.today().strftime("%Y-%m-%d")
        elif isinstance(when, date):
            when = when.strftime("%Y-%m-%d")
        df = pd.read_csv(EVENTS_PATH)
        new = {"date": str(when), "habit_name": str(habit_name), "user_name": str(user_name or '')}
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        df.to_csv(EVENTS_PATH, index=False)
    except Exception as e:
        logger.error(f"Error recording event: {e}")

def get_calendar_counts(month=None, year=None, user_name=None, habit_name=None):
    """Return a dict mapping day(int)->count of completion events for given month/year.
    If month/year are None, use current month.
    """
    try:
        _ensure_events()
        df = pd.read_csv(EVENTS_PATH)
        if df.empty:
            return {}
        df["date"] = df["date"].astype(str)
        df["_dt"] = pd.to_datetime(df["date"], errors="coerce")
        now = datetime.today()
        m = int(month or now.month)
        y = int(year or now.year)
        filt = df[df["_dt"].dt.month == m]
        filt = filt[filt["_dt"].dt.year == y]
        if user_name:
            filt = filt[filt["user_name"] == str(user_name)]
        if habit_name:
            filt = filt[filt["habit_name"] == str(habit_name)]
        if filt.empty:
            return {}
        counts = filt.groupby(filt["_dt"].dt.day).size().to_dict()
        return {int(k): int(v) for k, v in counts.items()}
    except Exception as e:
        logger.error(f"Error getting calendar counts: {e}")
        return {}


# --- Leaderboard helpers ---

def load_leaderboard(top_n=10):
    """Load top N users from leaderboard"""
    try:
        os.makedirs(os.path.dirname(LEADERBOARD_PATH), exist_ok=True)
        if not os.path.exists(LEADERBOARD_PATH):
            df = pd.DataFrame(columns=["user_name", "score", "last_updated"])
            df.to_csv(LEADERBOARD_PATH, index=False)
        df = pd.read_csv(LEADERBOARD_PATH)
        if df.empty:
            return []
        if "score" not in df.columns:
            df["score"] = 0
        df["score"] = df["score"].fillna(0).astype(int)
        df = df.sort_values("score", ascending=False)
        return df.head(top_n).to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error loading leaderboard: {e}")
        return []

def update_leaderboard(user_name, score):
    """Update or insert user score in leaderboard"""
    try:
        os.makedirs(os.path.dirname(LEADERBOARD_PATH), exist_ok=True)
        if not os.path.exists(LEADERBOARD_PATH):
            df = pd.DataFrame(columns=["user_name", "score", "last_updated"])
        else:
            df = pd.read_csv(LEADERBOARD_PATH)
        if "score" not in df.columns:
            df["score"] = 0
        exists = False
        user_name = str(user_name).strip()
        for i, row in df.iterrows():
            if str(row.get("user_name", "")).strip() == user_name:
                df.at[i, "score"] = int(score)
                df.at[i, "last_updated"] = str(date.today())
                exists = True
                break
        if not exists:
            new = {"user_name": user_name, "score": int(score), "last_updated": str(date.today())}
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        df.to_csv(LEADERBOARD_PATH, index=False)
        return True
    except Exception as e:
        logger.error(f"Error updating leaderboard: {e}")
        return False
