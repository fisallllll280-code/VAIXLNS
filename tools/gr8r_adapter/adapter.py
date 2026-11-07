"""Fail-closed Gr8r -> VAIXLNS VX intake adapter, standard-library only.
Connects local proposal intake to VCRE authorization primitives; no remote runtime execution.
"""
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.getenv('VAIXLNS_ADAPTER_DB', 'events.sqlite3')
HOST = os.getenv('VAIXLNS_ADAPTER_HOST', '127.0.0.1')
PORT = int(os.getenv('VAIXLNS_ADAPTER_PORT', '8765'))
KEY = os.getenv('VAIXLNS_ADAPTER_KEY', '')
MAX_BYTES = 16_384
LOCK = threading.Lock()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def initialize(path=DB):
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, request_digest TEXT NOT NULL, receipt TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS proposals (task_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, at_utc INTEGER NOT NULL, event_type TEXT NOT NULL, payload_digest TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL)')


def verify_input(data):
    if not isinstance(data, dict) or set(data) != {'task_id', 'title', 'source', 'requested_action'}:
        raise ValueError('invalid task envelope')
    if not isinstance(data['task_id'], str) or not (1 <= len(data['task_id']) <= 128):
        raise ValueError('invalid task_id')
    if not isinstance(data['title'], str) or not (1 <= len(data['title'].strip()) <= 500):
        raise ValueError('invalid title')
    if data['source'] != 'gr8r' or data['requested_action'] != 'propose':
        raise ValueError('only gr8r proposals accepted')


def intake(data, path=DB):
    verify_input(data)
    digest = hashlib.sha256(canonical(data).encode()).hexdigest()
    with LOCK, sqlite3.connect(path, timeout=5) as db:
        db.execute('BEGIN IMMEDIATE')
        prior = db.execute('SELECT request_digest, receipt FROM tasks WHERE task_id=?', (data['task_id'],)).fetchone()
        if prior:
            if prior[0] != digest:
                raise ValueError('idempotency conflict')
            return json.loads(prior[1])
        receipt = {'task_id': data['task_id'], 'receipt_id': str(uuid.uuid4()), 'status': 'PENDING_AUTHORIZATION', 'execution_performed': False, 'independent_verification': 'NOT_RUN', 'source': 'gr8r', 'request_sha256': digest}
        prev = db.execute('SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        previous_hash = prev[0] if prev else 'GENESIS'
        timestamp = int(time.time())
        event = {'task_id':data['task_id'], 'at_utc':timestamp, 'event_type':'TASK_PROPOSED', 'payload_digest':digest, 'previous_hash':previous_hash}
        event_hash = hashlib.sha256(canonical(event).encode()).hexdigest()
        db.execute('INSERT INTO events(task_id,at_utc,event_type,payload_digest,previous_hash,event_hash) VALUES(?,?,?,?,?,?)', (data['task_id'],timestamp,'TASK_PROPOSED',digest,previous_hash,event_hash))
        receipt['evidence_event_hash'] = event_hash
        receipt['vx_route'] = {'agent_id': 'VX-GR8R-INTAKE', 'target': 'vcre.agent_orchestration', 'connection': 'LOCAL_CONTRACT_ONLY', 'gate': 'HOLD'}
        db.execute('INSERT INTO proposals(task_id,payload) VALUES(?,?)', (data['task_id'], canonical(data)))
        db.execute('INSERT INTO tasks(task_id,request_digest,receipt) VALUES(?,?,?)', (data['task_id'],digest,canonical(receipt)))
        db.commit()
        return receipt


def authorize_proposal(data, envelope, *, registered_principal_id,
                       registered_capabilities, grant, now):
    """Trusted backend API only: validate a caller-supplied envelope and real grant.

    No grants are issued here; HTTP clients cannot invoke this function. The
    returned record authorizes delegation only, and does not execute a worker.
    Caller must authenticate registry/grant inputs outside this pure bridge.
    """
    from vcre.agent_orchestration import (
        TaskRecord, authorize_dispatch, canonical_fingerprint, OrchestrationError,
    )
    verify_input(data)
    if grant is None:
        raise OrchestrationError('explicit authority grant required')
    if (envelope.task_id != 'gr8r:' + data['task_id']
            or envelope.resource_ref != 'gr8r:' + data['task_id']
            or envelope.candidate_fingerprint != canonical_fingerprint(data)
            or envelope.role != 'INTEGRATION_ENGINEER'
            or envelope.capability_contract != ('gr8r:review-proposal',)
            or envelope.permitted_tools):
        raise OrchestrationError('Gr8r proposal binding or bounded review contract mismatch')
    record = TaskRecord(envelope)
    authorize_dispatch(record, registered_principal_id=registered_principal_id,
                       registered_capabilities=registered_capabilities,
                       grant=grant, now=now)
    return record


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def respond(self, status, value):
        payload = canonical(value).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != '/v1/tasks/intake':
            return self.respond(404, {'error': 'not_found'})
        if not hmac.compare_digest(self.headers.get('X-Adapter-Key', '').encode(), self.server.adapter_key.encode()):
            return self.respond(401, {'error': 'unauthorized'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not (0 < size <= MAX_BYTES):
                return self.respond(413, {'error': 'invalid_content_length'})
            body = self.rfile.read(size)
            if len(body) != size:
                return self.respond(400, {'error': 'incomplete_body'})
            data = json.loads(body)
            receipt = intake(data, self.server.adapter_db)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self.respond(400, {'error': 'invalid_request', 'reason': str(exc)[:120]})
        return self.respond(202, receipt)

    def do_GET(self):
        if self.path == '/health':
            return self.respond(200, {'status':'LOCAL_CONTRACT_ONLY','vx_connected':False,'vx_contract_available':True})
        return self.respond(404, {'error':'not_found'})


def create_server(*, path=DB, key=KEY, host=HOST, port=PORT):
    if host not in ('127.0.0.1', 'localhost'):
        raise ValueError('loopback host required; public service is not admitted')
    if not key or len(key) < 24:
        raise ValueError('Set a private adapter key of at least 24 characters')
    initialize(path)
    server = ThreadingHTTPServer((host, port), Handler)
    server.adapter_key = key
    server.adapter_db = path
    return server


if __name__ == '__main__':
    server = create_server()
    print(f'Local adapter listening at http://{HOST}:{PORT} (no VX worker execution)')
    server.serve_forever()
