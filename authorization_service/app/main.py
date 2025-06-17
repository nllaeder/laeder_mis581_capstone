from flask import Blueprint

main = Blueprint('main', __name__)

# Removed the '/' route to avoid conflict with app-level index route
