import unittest
import json
import os
import sys

# Add the parent directory to sys.path so we can import app and config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app, VOTE_FILE
from config import RESET_TOKEN

class VotingAppTestCase(unittest.TestCase):
    def setUp(self):
        # Set up a test client
        self.app = app.test_client()
        self.app.testing = True
        
        # Ensure a clean state for testing
        for f in [VOTE_FILE, "data/voters.txt", "data/meta.json"]:
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        for f in [VOTE_FILE, "data/voters.txt", "data/meta.json"]:
            if os.path.exists(f):
                os.remove(f)

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Kolik', response.data)

    def test_voting(self):
        # Vote for '0-5'
        response = self.app.post('/api/vote', 
                                 data=json.dumps({'option': '0-5'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['0-5'], 1)

        # Try to vote again (should be blocked by cookie)
        # Note: Flask test client handles cookies by default if created from app.test_client()
        response = self.app.post('/api/vote', 
                                 data=json.dumps({'option': '0-5'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 403)
        
        # Verify results still show only 1 vote
        response = self.app.get('/api/results')
        data = json.loads(response.data)
        self.assertEqual(data['0-5'], 1)

    def test_reset_correct_token(self):
        # First add a vote
        self.app.post('/api/vote', 
                      data=json.dumps({'option': '0-5'}),
                      content_type='application/json')
        
        # Reset with correct token
        response = self.app.post('/api/reset', 
                                 headers={'Authorization': RESET_TOKEN})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['votes']['0-5'], 0)

    def test_reset_incorrect_token(self):
        response = self.app.post('/api/reset', 
                                 headers={'Authorization': 'wrong-token'})
        self.assertEqual(response.status_code, 401)

    def test_invalid_vote(self):
        response = self.app.post('/api/vote', 
                                 data=json.dumps({'option': 'invalid-id'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
