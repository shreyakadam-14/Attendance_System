from supabase import create_client, Client
from datetime import datetime

# Supabase Configuration
# Replace with your Supabase URL and Anon Key
SUPABASE_URL = "https://utuwostgbayulslrgorj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0dXdvc3RnYmF5dWxzbHJnb3JqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc0NjY2ODksImV4cCI6MjA2MzA0MjY4OX0.CXWXfed1QO7sSwaciQwBUb1CB8ajgF0X6QAVfnMWX_c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

data = [
    {
        "id": "2004",
        "name": "Bette Porter",
        "major": "Robotics",
        "starting_year": 2017,
        "total_attendance": 7,
        "standing": "G",
        "year": 4,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
    {
        "id": "2005",
        "name": "Loli Bahia",
        "major": "Economics",
        "starting_year": 2021,
        "total_attendance": 12,
        "standing": "B",
        "year": 1,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
    {
        "id": "2006",
        "name": "Emma Chamberlain",
        "major": "Physics",
        "starting_year": 2020,
        "total_attendance": 7,
        "standing": "G",
        "year": 2,
        "last_attendance_time": "2022-12-11 00:54:34"
    }
]

print("Adding data to Supabase...")
for student_data in data:
    try:
        response = supabase.table('students').insert(student_data).execute()
        print(f"Inserted student {student_data['id']}: {response.data}")
    except Exception as e:
        print(f"Error inserting student {student_data['id']}: {e}")
print("Data addition complete.")