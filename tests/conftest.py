import pytest
import os
import sqlite3

os.environ["DB_PATH"] = ":memory:"

from server import app
from utils.database import init_db, get_conn

@pytest.fixture
def client():
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        yield client
