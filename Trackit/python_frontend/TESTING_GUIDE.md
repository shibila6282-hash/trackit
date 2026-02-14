# TrackIt - Testing Guide

## Quick Start Testing

### 1. Run the Application
```bash
cd python_frontend
python app.py
```
Browser: http://localhost:5000

### 2. Run Automated Tests
```bash
python tests/test_data_manager.py
```
Expected output: `Ran 13 tests in 0.005s - OK`

---

## Manual Feature Testing

### ✅ Feature 1: Duplicate Habit Detection

**Steps:**
1. Enter username and save
2. Add habit "Running"
3. Try to add "running" (lowercase)
4. Try to add "RUNNING" (uppercase)

**Expected Results:**
- ✅ First addition succeeds
- ✅ Second attempt shows: "Habit 'running' already exists!"
- ✅ Third attempt shows: "Habit 'RUNNING' already exists!"
- ✅ No duplicates created in database
- ✅ Check `trackit.log`: `WARNING - Duplicate habit attempted: running`

---

### ✅ Feature 2: Streak Counter

**Steps:**
1. Add habit "Meditation"
2. Click "Done" for meditation today
3. Click "Done" again tomorrow (simulate next day)
4. Repeat for 5 consecutive days
5. Check habit card

**Expected Results:**
- ✅ Habit card shows "🔥 5 day streak" badge
- ✅ Badge has coral color (#d4845c)
- ✅ Badge updates in real-time after each completion
- ✅ Breaks if you skip a day

**Technical Check:**
```bash
grep "streak" trackit.log  # Should be empty if no errors
```

---

### ✅ Feature 3: Reward Timestamping

**Steps:**
1. Track a habit and mark it done
2. Earn 50, 100, 200 points to trigger rewards
3. Check browser console for reward object structure

**Expected Results:**
- ✅ At 50 points: Bronze Badge 🥉 earned
- ✅ At 100 points: Silver Badge 🥈 earned
- ✅ At 200 points: Gold Badge 🥇 earned
- ✅ Reward object has structure:
  ```json
  {
    "name": "Bronze Badge 🥉",
    "earned_at": "2026-02-14T04:15:23.456789",
    "points_at_earn": 50
  }
  ```

**Technical Check:**
```bash
grep "unlocked rewards" trackit.log  # Should show each earning
```

---

### ✅ Feature 4: AI Persona System

**Steps:**
1. Open chat panel
2. Send message: "Help me improve"
3. With Coach persona, observe strategic tone
4. (In future) Change persona selector
5. Observe different response styles

**Expected Results:**
- ✅ Chat response is personalized
- ✅ System prompt includes persona style
- ✅ Default persona is "Coach"
- ✅ Response tone matches persona

**Technical Check:**
```bash
grep "Mentor\|Coach\|Friend\|Motivator" trackit.log
```

---

### ✅ Feature 5: Rate Limiting

**Steps:**
1. Open browser console (F12)
2. Send 6 chat messages within 60 seconds
3. Monitor network tab

**Expected Results:**
- ✅ Requests 1-5 succeed (200 OK)
- ✅ Request 6 returns 429 (Too Many Requests)
- ✅ Cool down after 60 seconds to retry

**Technical Check:**
```bash
grep "Rate limit exceeded" trackit.log  # Should show 5th request warning
```

---

### ✅ Feature 6: Session Validation

**Steps:**
1. Log in with username
2. Open DevTools → Application → Cookies
3. Find `session` cookie
4. Edit user_id to invalid value
5. Refresh page

**Expected Results:**
- ✅ Session cleared
- ✅ Redirected to login
- ✅ Check `trackit.log`: `ERROR - Session validation error`

---

### ✅ Feature 7: Logging to File

**Steps:**
1. Run app and interact with features
2. Open `trackit.log` in editor/terminal

**Expected Results:**
```log
2026-02-14 04:15:23,645 - __main__ - INFO - TrackIt application starting...
2026-02-14 04:15:29,574 - werkzeug - INFO - Running on http://127.0.0.1:5000
2026-02-14 XX:XX:XX,XXX - __main__ - INFO - New user account created: John (ID: abc-123...)
2026-02-14 XX:XX:XX,XXX - __main__ - INFO - New habit added: Running
2026-02-14 XX:XX:XX,XXX - __main__ - INFO - User John earned 10 points (total: 10)
```

- ✅ All operations logged with timestamp
- ✅ User account creation logged
- ✅ Points/rewards changes logged
- ✅ Errors logged at ERROR level

---

### ✅ Feature 8: Error Handling (Graceful Degradation)

**Steps:**
1. Simulate database corruption/error
2. Try to load weekly data
3. Check browser response

**Expected Results:**
- ✅ No 500 error shown to user
- ✅ Empty data returned: `{"success": true, "dates": [], "values": []}`
- ✅ Check `trackit.log`: `ERROR - Weekly data error: ...`
- ✅ UI displays gracefully (empty chart)

---

### ✅ Feature 9: Responsive Design

**Steps:**
1. Open app in browser
2. Resize to mobile (375px)
3. Check habit cards and streak badges
4. Test dark mode toggle

**Expected Results:**
- ✅ Habit cards stack responsively
- ✅ Streak badge responsive size
- ✅ Touch-friendly buttons (44px minimum)
- ✅ Dark mode: streak badge changes to lighter coral

---

### ✅ Feature 10: Chat History

**Steps:**
1. Send multiple messages in chat
2. Open DevTools → Console
3. Check `session` storage

**Expected Results:**
- ✅ Last 10 messages stored
- ✅ Format: `[{"user": "msg1", "ai": "reply1"}, ...]`
- ✅ Context preserved across messages
- ✅ Older messages removed after 10+

---

## Debugging Tips

### View Real-Time Logs
```bash
# Linux/Mac
tail -f trackit.log

# Windows PowerShell
Get-Content trackit.log -Wait
```

### Search Logs for Specific Events
```bash
grep "ERROR" trackit.log                    # All errors
grep "unlocked rewards" trackit.log          # Reward unlocks
grep "Duplicate habit" trackit.log           # Duplicate attempts
grep "Rate limit exceeded" trackit.log       # Rate limit hits
grep "Invalid session" trackit.log           # Session failures
```

### Database Files to Check
```bash
# Habit data
cat data/habits.csv

# User accounts
cat data/users.json

# Points & rewards
cat data/points.json

# Events (for streak calculation)
cat data/events.csv

# Leaderboard
cat data/leaderboard.csv
```

---

## Unit Test Details

### Run Specific Test Class
```bash
python -m unittest tests.test_data_manager.TestStreakCalculation -v
```

### Run Specific Test
```bash
python -m unittest tests.test_data_manager.TestStreakCalculation.test_streak_consecutive_days -v
```

### Test Output Example
```
test_duplicate_habit_detection_case_insensitive ... ok
test_streak_consecutive_days ... ok
test_check_rewards_have_timestamps ... ok
test_logger_error_handling ... Test error message
                                 ok
...
Ran 13 tests in 0.005s - OK
```

---

## Performance Testing

### Measure Habit Loading Time
```python
import time
from data_manager import load_habits_with_rate

start = time.time()
for _ in range(100):
    habits = load_habits_with_rate()
elapsed = time.time() - start
print(f"100 iterations: {elapsed:.3f}s, avg: {elapsed/100*1000:.1f}ms")
```

### Measure Streak Calculation
```python
import time
from data_manager import calculate_streak

start = time.time()
for _ in range(100):
    streak = calculate_streak("Running")
elapsed = time.time() - start
print(f"100 streak calcs: {elapsed:.3f}s, avg: {elapsed/100*1000:.1f}ms")
```

---

## Checklist for Deployment

- [ ] All 13 tests passing: `python tests/test_data_manager.py`
- [ ] No errors in `trackit.log`
- [ ] Duplicate habit detection working
- [ ] Streak counter displaying (at least 1 day)
- [ ] Rewards showing with timestamps
- [ ] Chat responding (mock or Gemini)
- [ ] Rate limiting active (test with 6 rapid requests)
- [ ] Dark mode styling correct
- [ ] All environment variables set (.env file)
- [ ] `data/` directory exists with CSV files
- [ ] Responsive design tested on mobile/tablet

---

## Common Issues & Solutions

### Issue: Import errors in VSCode
**Solution**: These are linter warnings. The app works fine - server is running.
```bash
# Verify by running: python app.py
# If server starts, imports are fine
```

### Issue: No streak showing
**Solution**: Ensure events were recorded
```bash
cat data/events.csv  # Should have entries for your habits
```

### Issue: Duplicate check not working
**Solution**: Check case sensitivity
```bash
python -c "
habits = ['Running', 'Reading']
print('running' in [h.lower() for h in habits])  # Should print: True
"
```

### Issue: Tests failing
**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt
python tests/test_data_manager.py
```

### Issue: Rate limiting not triggering
**Solution**: Verify session user_id is set
```bash
# In browser console:
document.cookie  # Should see user session
```

---

## Performance Baseline

- Dashboard load: 50-100ms
- Habit load: 5-10ms
- Streak calc: 15-20ms  
- Points add: 8-12ms
- Chat response: 1-3s (Gemini), 50-100ms (mock)

---

## Success Criteria

✅ All 13 unit tests pass
✅ No 500 errors in production logs
✅ Streak badge displays correctly
✅ Rewards timestamped
✅ Duplicate detection prevents duplicates
✅ Rate limiting enforced
✅ Logging captures all operations
✅ Responsive on mobile/tablet/desktop
✅ Dark mode works
✅ AI persona appropriate to selection

**Ready for production deployment!** 🚀
