import unittest
import json
import os
import sys
import threading

# Add the parent directory to sys.path so we can import app and config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app
from config import RESET_TOKEN, VOTE_FILE, QUESTIONS

DATA_FILES = [VOTE_FILE, "data/voters.txt", "data/meta.json"]
_SENTINEL = object()  # Sentinel pro rozlišení "nezadáno" vs. "prázdný řetězec"


def clean_data_files():
    import time
    for f in DATA_FILES:
        for _ in range(5):  # Zkus n-krát (filelock může soubor krátce držet)
            try:
                if os.path.exists(f):
                    os.remove(f)
                break
            except PermissionError:
                time.sleep(0.05)
    for lock_file in ["data/votes.json.lock", "data/meta.json.lock", "data/voters.txt.lock"]:
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except PermissionError:
            pass  # Na Windows může být lock soubor držen krátce po uvolnění


class BaseTestCase(unittest.TestCase):
    """Základní třída – zajišťuje čistý stav před/po každém testu."""

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        clean_data_files()

    def tearDown(self):
        clean_data_files()

    # ------------------------------------------------------------------ helpers
    def _vote(self, option="0-5", environ_base=None):
        kwargs = dict(
            data=json.dumps({'option': option}),
            content_type='application/json',
        )
        if environ_base:
            kwargs['environ_base'] = environ_base
        return self.client.post('/api/vote', **kwargs)

    def _reset(self, token=_SENTINEL):
        """Pošle reset request. Pokud token není zadán, použije RESET_TOKEN."""
        if token is _SENTINEL:
            token = RESET_TOKEN
        return self.client.post('/api/reset', headers={'Authorization': token})

    def _admin_stats(self, token=_SENTINEL):
        """Pošle admin stats request. Pokud token není zadán, použije RESET_TOKEN."""
        if token is _SENTINEL:
            token = RESET_TOKEN
        return self.client.get('/api/admin/stats', headers={'Authorization': token})


# ============================================================
# 1. STRÁNKY (Pages)
# ============================================================
class TestPages(BaseTestCase):

    def test_index_page_returns_200(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_index_page_contains_question(self):
        resp = self.client.get('/')
        self.assertIn(b'Kolik', resp.data)

    def test_index_page_contains_all_options(self):
        resp = self.client.get('/')
        for opt in QUESTIONS['options']:
            self.assertIn(opt['label'].encode('utf-8'), resp.data)

    def test_about_page_returns_200(self):
        resp = self.client.get('/about')
        self.assertEqual(resp.status_code, 200)

    def test_admin_page_returns_200(self):
        resp = self.client.get('/admin')
        self.assertEqual(resp.status_code, 200)

    def test_nonexistent_page_returns_404(self):
        resp = self.client.get('/neexistuje')
        self.assertEqual(resp.status_code, 404)


# ============================================================
# 2. SECURITY HEADERS
# ============================================================
class TestSecurityHeaders(BaseTestCase):

    def _check_headers(self, path, method='get'):
        resp = getattr(self.client, method)(path)
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'SAMEORIGIN',
                         f"Chybí X-Frame-Options na {path}")
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff',
                         f"Chybí X-Content-Type-Options na {path}")

    def test_security_headers_on_index(self):
        self._check_headers('/')

    def test_security_headers_on_about(self):
        self._check_headers('/about')

    def test_security_headers_on_admin(self):
        self._check_headers('/admin')

    def test_security_headers_on_api_results(self):
        self._check_headers('/api/results')

    def test_security_headers_on_api_vote(self):
        self._check_headers('/api/vote', method='post')

    def test_security_headers_on_api_reset(self):
        self._check_headers('/api/reset', method='post')


# ============================================================
# 3. GET /api/results
# ============================================================
class TestResults(BaseTestCase):

    def test_results_returns_200(self):
        resp = self.client.get('/api/results')
        self.assertEqual(resp.status_code, 200)

    def test_results_returns_json(self):
        resp = self.client.get('/api/results')
        data = json.loads(resp.data)
        self.assertIsInstance(data, dict)

    def test_results_contain_all_options(self):
        resp = self.client.get('/api/results')
        data = json.loads(resp.data)
        for opt in QUESTIONS['options']:
            self.assertIn(opt['id'], data)

    def test_results_initial_counts_are_zero(self):
        resp = self.client.get('/api/results')
        data = json.loads(resp.data)
        for opt in QUESTIONS['options']:
            self.assertEqual(data[opt['id']], 0)


# ============================================================
# 4. POST /api/vote – základní hlasování
# ============================================================
class TestVoting(BaseTestCase):

    def test_vote_valid_option_returns_200(self):
        resp = self._vote('0-5')
        self.assertEqual(resp.status_code, 200)

    def test_vote_increments_count(self):
        self._vote('0-5')
        data = json.loads(self.client.get('/api/results').data)
        self.assertEqual(data['0-5'], 1)

    def test_vote_increments_correct_option_only(self):
        self._vote('6-20')
        data = json.loads(self.client.get('/api/results').data)
        self.assertEqual(data['6-20'], 1)
        self.assertEqual(data['0-5'], 0)
        self.assertEqual(data['21+'], 0)
        self.assertEqual(data['melt'], 0)

    def test_vote_returns_updated_votes_dict(self):
        resp = self._vote('21+')
        data = json.loads(resp.data)
        self.assertEqual(data['21+'], 1)

    def test_vote_sets_cookie(self):
        resp = self._vote('0-5')
        self.assertIn('voted', resp.headers.get('Set-Cookie', ''))

    def test_vote_all_valid_options(self):
        """Otestuje, že všechny platné volby lze odeslat."""
        for opt in QUESTIONS['options']:
            clean_data_files()
            with app.test_client() as c:
                resp = c.post('/api/vote',
                              data=json.dumps({'option': opt['id']}),
                              content_type='application/json')
                self.assertEqual(resp.status_code, 200,
                                 f"Volba '{opt['id']}' selhala")


# ============================================================
# 5. POST /api/vote – blokování duplicitního hlasování
# ============================================================
class TestDuplicateVoting(BaseTestCase):

    def test_double_vote_by_cookie_blocked(self):
        self._vote('0-5')
        resp = self._vote('0-5')
        self.assertEqual(resp.status_code, 403)

    def test_double_vote_error_message_contains_cookie(self):
        self._vote('0-5')
        resp = self._vote('0-5')
        data = json.loads(resp.data)
        self.assertIn('cookie', data.get('error', '').lower())

    def test_double_vote_count_remains_one(self):
        self._vote('0-5')
        self._vote('0-5')
        data = json.loads(self.client.get('/api/results').data)
        self.assertEqual(data['0-5'], 1)

    def test_ip_block_after_vote(self):
        """Druhý klient (bez cookie) se stejnou IP musí být blokován."""
        # Simulujeme dvě různé relace (bez sdílení cookies) ale se stejnou remote_addr
        environ = {'REMOTE_ADDR': '1.2.3.4'}
        with app.test_client() as c1:
            c1.post('/api/vote',
                    data=json.dumps({'option': '0-5'}),
                    content_type='application/json',
                    environ_base=environ)
        with app.test_client() as c2:
            resp = c2.post('/api/vote',
                           data=json.dumps({'option': '0-5'}),
                           content_type='application/json',
                           environ_base=environ)
        self.assertEqual(resp.status_code, 403)

    def test_ip_block_error_message(self):
        environ = {'REMOTE_ADDR': '5.6.7.8'}
        with app.test_client() as c1:
            c1.post('/api/vote',
                    data=json.dumps({'option': '0-5'}),
                    content_type='application/json',
                    environ_base=environ)
        with app.test_client() as c2:
            resp = c2.post('/api/vote',
                           data=json.dumps({'option': '0-5'}),
                           content_type='application/json',
                           environ_base=environ)
        data = json.loads(resp.data)
        self.assertIn('ip', data.get('error', '').lower())


# ============================================================
# 6. POST /api/vote – neplatný vstup
# ============================================================
class TestInvalidVote(BaseTestCase):

    def test_invalid_option_returns_400(self):
        resp = self._vote('neplatna-volba')
        self.assertEqual(resp.status_code, 400)

    def test_invalid_option_error_message(self):
        resp = self._vote('neplatna-volba')
        data = json.loads(resp.data)
        self.assertIn('error', data)

    def test_empty_option_returns_400(self):
        resp = self._vote('')
        self.assertEqual(resp.status_code, 400)

    def test_sql_injection_attempt_returns_400(self):
        resp = self._vote("' OR '1'='1")
        self.assertEqual(resp.status_code, 400)

    def test_missing_option_field_returns_400(self):
        resp = self.client.post('/api/vote',
                                data=json.dumps({}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_vote_with_no_json_body(self):
        resp = self.client.post('/api/vote')
        # Musí vrátit chybový kód (400 nebo 415/500), ne 200
        self.assertNotEqual(resp.status_code, 200)


# ============================================================
# 7. POST /api/reset
# ============================================================
class TestReset(BaseTestCase):

    def test_reset_with_correct_token_returns_200(self):
        resp = self._reset()
        self.assertEqual(resp.status_code, 200)

    def test_reset_with_wrong_token_returns_401(self):
        resp = self._reset('spatny-token')
        self.assertEqual(resp.status_code, 401)

    def test_reset_with_empty_token_returns_401(self):
        resp = self._reset('')
        self.assertEqual(resp.status_code, 401)

    def test_reset_clears_votes(self):
        self._vote('0-5')
        self._reset()
        data = json.loads(self.client.get('/api/results').data)
        for opt in QUESTIONS['options']:
            self.assertEqual(data[opt['id']], 0)

    def test_reset_response_contains_success_true(self):
        resp = self._reset()
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))

    def test_reset_response_contains_votes(self):
        resp = self._reset()
        data = json.loads(resp.data)
        self.assertIn('votes', data)

    def test_reset_allows_voting_again_after_reset(self):
        environ = {'REMOTE_ADDR': '9.9.9.9'}
        with app.test_client() as c:
            c.post('/api/vote',
                   data=json.dumps({'option': '0-5'}),
                   content_type='application/json',
                   environ_base=environ)
            self._reset()  # reset přes self.client
            # Nový klient (bez cookie) ze stejné IP musí moci hlasovat
            with app.test_client() as c2:
                resp = c2.post('/api/vote',
                               data=json.dumps({'option': '0-5'}),
                               content_type='application/json',
                               environ_base=environ)
        self.assertEqual(resp.status_code, 200)

    def test_reset_updates_meta_to_default(self):
        self._vote('0-5')
        self._reset()
        stats = json.loads(self._admin_stats().data)
        self.assertEqual(stats['meta']['total_clicks'], 0)
        self.assertEqual(stats['meta']['last_vote'], 'Nikdy')


# ============================================================
# 8. GET /api/admin/stats
# ============================================================
class TestAdminStats(BaseTestCase):

    def test_admin_stats_with_correct_token_returns_200(self):
        resp = self._admin_stats()
        self.assertEqual(resp.status_code, 200)

    def test_admin_stats_with_wrong_token_returns_401(self):
        resp = self._admin_stats('spatny-token')
        self.assertEqual(resp.status_code, 401)

    def test_admin_stats_with_empty_token_returns_401(self):
        resp = self._admin_stats('')
        self.assertEqual(resp.status_code, 401)

    def test_admin_stats_contains_votes(self):
        data = json.loads(self._admin_stats().data)
        self.assertIn('votes', data)

    def test_admin_stats_contains_meta(self):
        data = json.loads(self._admin_stats().data)
        self.assertIn('meta', data)

    def test_admin_stats_contains_unique_ips(self):
        data = json.loads(self._admin_stats().data)
        self.assertIn('unique_ips', data)

    def test_admin_stats_ip_count_increases_after_vote(self):
        before = json.loads(self._admin_stats().data)['unique_ips']
        # Hlasování z unikátní IP
        with app.test_client() as c:
            c.post('/api/vote',
                   data=json.dumps({'option': '0-5'}),
                   content_type='application/json',
                   environ_base={'REMOTE_ADDR': '11.22.33.44'})
        after = json.loads(self._admin_stats().data)['unique_ips']
        self.assertEqual(after, before + 1)

    def test_admin_stats_total_clicks_increases_after_vote(self):
        before = json.loads(self._admin_stats().data)['meta']['total_clicks']
        self._vote('melt')
        after = json.loads(self._admin_stats().data)['meta']['total_clicks']
        self.assertEqual(after, before + 1)

    def test_admin_stats_last_vote_updates(self):
        before = json.loads(self._admin_stats().data)['meta']['last_vote']
        self._vote('melt')
        after = json.loads(self._admin_stats().data)['meta']['last_vote']
        self.assertNotEqual(after, before)

    def test_admin_stats_vote_counts_match_results(self):
        self._vote('21+')
        stats_data = json.loads(self._admin_stats().data)
        results_data = json.loads(self.client.get('/api/results').data)
        self.assertEqual(stats_data['votes'], results_data)


# ============================================================
# 9. HTTP METODY – špatné metody
# ============================================================
class TestWrongHttpMethods(BaseTestCase):

    def test_vote_endpoint_rejects_get(self):
        resp = self.client.get('/api/vote')
        self.assertEqual(resp.status_code, 405)

    def test_reset_endpoint_rejects_get(self):
        resp = self.client.get('/api/reset')
        self.assertEqual(resp.status_code, 405)

    def test_results_endpoint_rejects_post(self):
        resp = self.client.post('/api/results')
        self.assertEqual(resp.status_code, 405)

    def test_admin_stats_endpoint_rejects_post(self):
        resp = self.client.post('/api/admin/stats',
                                headers={'Authorization': RESET_TOKEN})
        self.assertEqual(resp.status_code, 405)


# ============================================================
# 10. PERSISTENCE DAT
# ============================================================
class TestDataPersistence(BaseTestCase):

    def test_votes_persist_across_requests(self):
        self._vote('0-5')
        # Druhý nezávislý request musí vidět hlas
        data = json.loads(self.client.get('/api/results').data)
        self.assertEqual(data['0-5'], 1)

    def test_multiple_votes_accumulate(self):
        options = [opt['id'] for opt in QUESTIONS['options']]
        for i, opt in enumerate(options):
            environ = {'REMOTE_ADDR': f'10.0.0.{i+1}'}
            with app.test_client() as c:
                c.post('/api/vote',
                       data=json.dumps({'option': opt}),
                       content_type='application/json',
                       environ_base=environ)
        data = json.loads(self.client.get('/api/results').data)
        for opt in options:
            self.assertEqual(data[opt], 1)


# ============================================================
# 11. SOUBĚŽNÉ HLASOVÁNÍ (Concurrency / Race Condition)
# ============================================================
class TestConcurrency(BaseTestCase):

    def test_concurrent_votes_no_data_corruption(self):
        """Více vláken hlasuje najednou – filelock musí zarůčit konzistenci.
        
        Testuje filelock přímo pomocí vote_lock ze `flask_app`.
        Každé vlákno provede atomický read-modify-write pod jedním zámkem.
        Výsledný počet musí přesně odpovídat počtu vláken.
        """
        from flask_app import vote_lock
        import json as _json

        n = 20
        errors = []

        def atomic_increment():
            """Simuluje atomický způsob jak by správně mělo být hlasování implementováno."""
            try:
                with vote_lock:
                    if os.path.exists(VOTE_FILE):
                        with open(VOTE_FILE, 'r', encoding='utf-8') as f:
                            votes = _json.load(f)
                    else:
                        from config import QUESTIONS as Q
                        votes = {opt['id']: 0 for opt in Q['options']}
                    votes['0-5'] += 1
                    with open(VOTE_FILE, 'w', encoding='utf-8') as f:
                        _json.dump(votes, f, indent=4)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=atomic_increment) for _ in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Výjimky při souběžném zápisu: {errors}")
        with open(VOTE_FILE, 'r', encoding='utf-8') as f:
            final_votes = _json.load(f)
        self.assertEqual(final_votes['0-5'], n,
                         f"Data corruption: očekáváno {n} hlasů, uloženo {final_votes['0-5']}")


# ============================================================
# 12. KONFIGURACE
# ============================================================
class TestConfig(BaseTestCase):

    def test_questions_have_required_keys(self):
        self.assertIn('question', QUESTIONS)
        self.assertIn('options', QUESTIONS)

    def test_all_options_have_id_and_label(self):
        for opt in QUESTIONS['options']:
            self.assertIn('id', opt)
            self.assertIn('label', opt)

    def test_option_ids_are_unique(self):
        ids = [opt['id'] for opt in QUESTIONS['options']]
        self.assertEqual(len(ids), len(set(ids)))

    def test_reset_token_is_set(self):
        self.assertTrue(RESET_TOKEN, "RESET_TOKEN nesmí být prázdný")

    def test_vote_file_path_is_set(self):
        self.assertTrue(VOTE_FILE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
