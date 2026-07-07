import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app import app
app.run(debug=False, host="0.0.0.0", port=5000)
