from lineup_app import app
from lineup_app.views import socketio
socketio.run(app,debug=True)
