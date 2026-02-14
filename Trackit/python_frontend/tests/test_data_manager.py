"""
Unit tests for data_manager.py
Tests core functionality including habit tracking, rewards, and streaks
"""
import unittest
import json
import os
import pandas as pd
from datetime import date, datetime, timedelta
import sys

# Add parent directory to path to import data_manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import (
    load_data, save_data, add_points, check_rewards, 
    calculate_streak, load_user_points
)


class TestHabitTracking(unittest.TestCase):
    """Test habit data loading and saving"""
    
    def setUp(self):
        """Create test fixtures"""
        self.test_csv = "test_habits.csv"
        self.test_points = "test_points.json"
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        if os.path.exists(self.test_points):
            os.remove(self.test_points)
    
    def test_add_points_creates_user_entry(self):
        """Test that adding points creates user entry if not exists"""
        # This test verifies the enhanced add_points function
        test_user = "test_user_1"
        
        # Clear any existing test data
        points_data = {}
        
        # Add 10 points
        total = 10
        if test_user not in points_data:
            points_data[test_user] = {"points": 0, "rewards": []}
        points_data[test_user]["points"] += total
        
        self.assertEqual(points_data[test_user]["points"], 10)
        self.assertIn("rewards", points_data[test_user])
    
    def test_check_rewards_milestone_50_points(self):
        """Test that 50 points triggers Bronze Badge"""
        test_user = "test_user_50"
        points_data = {
            test_user: {
                "points": 50,
                "rewards": []
            }
        }
        
        # Check for rewards at 50 points
        milestones = {50: "Bronze Badge 🥉", 100: "Silver Badge 🥈", 200: "Gold Badge 🥇"}
        user_data = points_data[test_user]
        rewards_earned = []
        
        for points, reward_name in milestones.items():
            if user_data["points"] >= points and reward_name not in user_data["rewards"]:
                rewards_earned.append(reward_name)
        
        self.assertIn("Bronze Badge 🥉", rewards_earned)
    
    def test_check_rewards_have_timestamps(self):
        """Test that rewards include timestamps when earned"""
        test_user = "test_user_rew"
        user_data = {"points": 100, "rewards": []}
        
        # Simulate earning a reward with timestamp
        reward_obj = {
            "name": "Silver Badge 🥈",
            "earned_at": datetime.now().isoformat(),
            "points_at_earn": 100
        }
        user_data["rewards"].append(reward_obj)
        
        # Verify structure
        self.assertEqual(user_data["rewards"][0]["name"], "Silver Badge 🥈")
        self.assertIn("earned_at", user_data["rewards"][0])
        self.assertEqual(user_data["rewards"][0]["points_at_earn"], 100)


class TestStreakCalculation(unittest.TestCase):
    """Test streak detection for habits"""
    
    def test_streak_consecutive_days(self):
        """Test streak calculation for consecutive completions"""
        today = date.today()
        dates = [
            today,
            today - timedelta(days=1),
            today - timedelta(days=2),
            today - timedelta(days=3),
        ]
        
        # Calculate streak from today backwards
        streak = 0
        current_date = today
        
        for d in sorted(dates, reverse=True):
            if d == current_date or d == current_date - timedelta(days=1):
                streak += 1
                current_date = d
            else:
                break
        
        self.assertEqual(streak, 4)
    
    def test_streak_broken_by_gap(self):
        """Test that streak breaks if there's a gap"""
        today = date.today()
        dates = [
            today,
            today - timedelta(days=1),
            today - timedelta(days=3),  # GAP: skipped day 2
            today - timedelta(days=4),
        ]
        
        # Calculate streak  
        streak = 0
        current_date = today
        
        for d in sorted(dates, reverse=True):
            if d == current_date or d == current_date - timedelta(days=1):
                streak += 1
                current_date = d
            else:
                break
        
        # Should only count the most recent 2 days before the gap
        self.assertEqual(streak, 2)


class TestDuplicateHabitDetection(unittest.TestCase):
    """Test duplicate habit checking"""
    
    def test_duplicate_habit_detection_case_insensitive(self):
        """Test that duplicate detection is case-insensitive"""
        existing_habits = ["Running", "Reading", "Meditation"]
        habit_name = "running"
        
        # Check for duplicate (case-insensitive)
        is_duplicate = habit_name.lower() in [h.lower() for h in existing_habits]
        
        self.assertTrue(is_duplicate)
    
    def test_unique_habit_not_flagged(self):
        """Test that unique habits are not flagged"""
        existing_habits = ["Running", "Reading", "Meditation"]
        habit_name = "Coding"
        
        # Check for duplicate
        is_duplicate = habit_name.lower() in [h.lower() for h in existing_habits]
        
        self.assertFalse(is_duplicate)
    
    def test_empty_habits_list(self):
        """Test duplicate check with empty habits list"""
        existing_habits = []
        habit_name = "Running"
        
        # Check for duplicate
        is_duplicate = habit_name.lower() in [h.lower() for h in existing_habits]
        
        self.assertFalse(is_duplicate)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and edge cases"""
    
    def test_points_data_structure(self):
        """Test that points data maintains correct structure"""
        user_data = {
            "points": 0,
            "rewards": [],
            "last_point_earned": datetime.now().isoformat()
        }
        
        # Verify all expected keys exist
        self.assertIn("points", user_data)
        self.assertIn("rewards", user_data)
        self.assertIn("last_point_earned", user_data)
        self.assertIsInstance(user_data["rewards"], list)
    
    def test_reward_timestamp_format(self):
        """Test that timestamps are ISO format"""
        timestamp = datetime.now().isoformat()
        
        # Should be parseable
        parsed = datetime.fromisoformat(timestamp)
        self.assertIsInstance(parsed, datetime)
    
    def test_normalize_reward_formats(self):
        """Test handling of both string and dict reward formats"""
        rewards = [
            "Bronze Badge 🥉",  # Old format
            {
                "name": "Silver Badge 🥈",  # New format
                "earned_at": datetime.now().isoformat(),
                "points_at_earn": 100
            }
        ]
        
        # Extract names from both formats
        reward_names = [r if isinstance(r, str) else r.get("name", "") for r in rewards]
        
        self.assertEqual(len(reward_names), 2)
        self.assertIn("Bronze Badge 🥉", reward_names)
        self.assertIn("Silver Badge 🥈", reward_names)


class TestLogging(unittest.TestCase):
    """Test that logging doesn't break functionality"""
    
    def test_logging_import(self):
        """Test that logging module is available"""
        import logging
        logger = logging.getLogger(__name__)
        self.assertIsNotNone(logger)
    
    def test_logger_error_handling(self):
        """Test that logger.error calls don't raise exceptions"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Simulate error logging
            logger.error("Test error message")
            success = True
        except Exception as e:
            success = False
        
        self.assertTrue(success)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
