import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_manager import load_data, add_new_habit, mark_habit_done, get_weekly_data
import pandas as pd

TEST_NAME = "Assistant Test Habit"

print('--- Current habits ---')
print(load_data().to_string(index=False))

print('\n--- Adding habit:', TEST_NAME, '---')
print(add_new_habit(TEST_NAME))

print('\n--- After add ---')
print(load_data().to_string(index=False))

print('\n--- Marking Done ---')
print(mark_habit_done(TEST_NAME))

print('\n--- After done ---')
print(load_data().to_string(index=False))

print('\n--- Weekly Data ---')
dates, results = get_weekly_data()
print('dates=', dates)
print('results=', results)
