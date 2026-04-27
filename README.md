git clone https://github.com/NourAawar/VolleyIQ.git

cd VolleyIQ

pip install -r requirements.txt

python manage.py runserver

Then open: http://127.0.0.1:8000

ROLE DEFINITIONS

Club Manager:
- Manage tournaments (create, delete, schedule generation)
- Manage teams (create, delete, assign coaches, register/remove teams)
- Manage matches (edit schedule, venue, registration)
- Send system-wide announcements

Coach:
- Access only assigned team
- View team performance insights
- Update match scores
- Assign tasks to players
- Record attendance and manage availability
- Send team messages

Player:
- View tournaments and team information
- View personal performance statistics
- View assigned tasks
- View match participation and announcements