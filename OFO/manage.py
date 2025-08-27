# OFO/manage.py
import os
# Vì manage.py nằm trong OFO, nó import trực tiếp create_app từ __init__.py
from __init__ import create_app

app = create_app()

if __name__ == '__main__':
    app.run()