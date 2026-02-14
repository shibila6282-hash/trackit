import unittest
import tempfile
import os
import shutil

import python_frontend.data_manager as dm


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.datafile = os.path.join(self.tmpdir, "habits.csv")
        dm.DATA_PATH = self.datafile

    def tearDown(self):
        try:
            if os.path.exists(self.datafile):
                os.remove(self.datafile)
        except Exception:
            pass
        try:
            shutil.rmtree(self.tmpdir)
        except Exception:
            pass

    def test_load_creates_file_and_columns(self):
        df = dm.load_data()
        self.assertTrue(os.path.exists(self.datafile))
        self.assertIn("habit_name", df.columns)

    def test_add_new_and_mark_done(self):
        res = dm.add_new_habit("testhabit")
        self.assertIn("added successfully", res)
        df = dm.load_data()
        self.assertIn("testhabit", list(df["habit_name"]))

        # ensure last_date column is string-typed to avoid float->string assignment issues
        df = dm.load_data()
        df["last_date"] = df["last_date"].fillna("").astype(str)
        dm.save_data(df)

        res2 = dm.mark_habit_done("testhabit")
        self.assertIn("Updated successfully", res2)
        df = dm.load_data()
        row = df[df["habit_name"] == "testhabit"].iloc[0]
        self.assertEqual(int(row["days_completed"]), 1)

    def test_skip_habit(self):
        dm.add_new_habit("skipit")
        df = dm.load_data().set_index("habit_name")
        before = int(df.at["skipit", "total_days"])
        dm.skip_habit("skipit")
        after = int(dm.load_data().set_index("habit_name").at["skipit", "total_days"])
        self.assertEqual(after, before + 1)

    def test_get_weekly_data(self):
        dm.add_new_habit("w")
        dates, results = dm.get_weekly_data()
        self.assertEqual(len(dates), 7)
        self.assertEqual(len(results), 7)
        for _, val in results:
            self.assertTrue(0 <= val <= 100)

    def test_gui_imports_cleanly(self):
        import importlib
        importlib.import_module("python_frontend.gui")


if __name__ == "__main__":
    unittest.main()
