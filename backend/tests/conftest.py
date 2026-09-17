import os
import tempfile

_TEST_DIR = tempfile.mkdtemp(prefix="salesiq_test_")
os.environ["SALESIQ_DATA_DIR"] = _TEST_DIR
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DIR}/test.db"
