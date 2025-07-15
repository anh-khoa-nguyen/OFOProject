import unittest
import dao

class TestLogin(unittest.TestCase):

    def test1(self):
        self.assertTrue(dao.auth_user("user", 123));

    def test2(self):
        self.assertFalse(dao.auth_user("user", 355));

if __name__ == "__main__":
    unittest.main