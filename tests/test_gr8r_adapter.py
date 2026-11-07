import os
import sqlite3
import tempfile
import unittest
from tools.gr8r_adapter.adapter import initialize, intake

SAMPLE = {'task_id':'task-001', 'title':'Review PR', 'source':'gr8r','requested_action':'propose'}

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'test.sqlite')
        initialize(self.path)
    def tearDown(self):
        self.tmp.cleanup()
    def test_intake_no_execution(self):
        receipt = intake(SAMPLE, self.path)
        self.assertFalse(receipt['execution_performed'])
        self.assertEqual(receipt['status'],'PENDING_AUTHORIZATION')
    def test_idempotent(self):
        self.assertEqual(intake(SAMPLE,self.path),intake(SAMPLE,self.path))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0],1)
    def test_conflict(self):
        intake(SAMPLE,self.path)
        with self.assertRaisesRegex(ValueError,'idempotency conflict'):
            intake({**SAMPLE,'title':'Changed'},self.path)
    def test_fail_closed(self):
        with self.assertRaises(ValueError):
            intake({**SAMPLE,'requested_action':'execute'},self.path)
        with self.assertRaises(ValueError):
            intake({**SAMPLE,'source':'unknown'},self.path)
    def test_evidence_chain(self):
        a = intake(SAMPLE,self.path)
        b = intake({**SAMPLE,'task_id':'task-002'},self.path)
        with sqlite3.connect(self.path) as db:
            rows = db.execute('SELECT previous_hash,event_hash FROM events ORDER BY seq').fetchall()
        self.assertEqual(rows[0][0], 'GENESIS')
        self.assertEqual(rows[1][0], rows[0][1])
        self.assertEqual(b['evidence_event_hash'],rows[1][1])

if __name__ == '__main__': unittest.main()
