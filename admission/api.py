"""Validated immutable values and controller-side local admission helpers.

Construction validates structure, not authenticity or semantic correctness.
Only evaluate authenticates evidence. Producer commands are trusted controller
configuration; this adapter is not a sandbox and never claims a checked proof.
"""
from dataclasses import dataclass
import base64
import hmac
import os
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from tools import admission_gate as gate


def _value(value):
    return value.to_dict() if isinstance(value, Document) else value


@dataclass(frozen=True, init=False)
class Document:
    canonical: bytes

    def __init__(self, value):
        data = gate.load_json(value) if isinstance(value, (str, bytes)) else _value(value)
        self.validate(data)
        object.__setattr__(self, "canonical", gate.canonical(data))

    def validate(self, data):
        raise NotImplementedError

    def to_dict(self):
        return gate.load_json(self.canonical)

    @property
    def digest(self):
        return gate.sha(self.canonical)


@dataclass(frozen=True, init=False)
class Policy(Document):
    def validate(self, data):
        # Placeholder verification keys validate policy shape only, never trust.
        try:
            keys = {data['domains'][d]['producer']: bytes([i + 1]) * 32
                    for i, d in enumerate(gate.DOMAINS)}
            gate.validate_policy(data, keys)
        except (KeyError, TypeError) as error:
            raise gate.Invalid('invalid policy structure') from error


@dataclass(frozen=True, init=False)
class Manifest(Document):
    def validate(self, data):
        gate.exact(data, gate.MANIFEST_FIELDS)
        if type(data['version']) is not int or data['version'] != 1:
            raise gate.Invalid('unsupported manifest version')
        if type(data['epoch']) is not int or data['epoch'] < 0:
            raise gate.Invalid('invalid authority epoch')
        for name in ('repository', 'target', 'request', 'actor'):
            gate.identifier(data[name])
        if not data['target'].startswith('refs/heads/'):
            raise gate.Invalid('target must be a branch')
        for name in ('base', 'candidate', 'tree'):
            gate.digest(data[name], 40)
        for name in ('policy', *gate.PINS):
            gate.digest(data[name])


@dataclass(frozen=True, init=False)
class Receipt(Document):
    def validate(self, data):
        gate.exact(data, {'domain', 'producer', 'kind', 'manifest', 'artifact', 'status', 'mac'})
        if data['domain'] not in gate.DOMAINS or data['status'] not in ('PASS', 'FAIL', 'PENDING'):
            raise gate.Invalid('invalid receipt domain or status')
        if data['kind'] not in ('checked-proof', 'finite-check', 'bounded-test'):
            raise gate.Invalid('invalid evidence kind')
        gate.identifier(data['producer'])
        for name in ('manifest', 'artifact', 'mac'):
            gate.digest(data[name])


@dataclass(frozen=True, init=False)
class Bundle(Document):
    def validate(self, data):
        gate.exact(data, {'manifest', 'receipts'})
        Manifest(data['manifest'])
        if type(data['receipts']) is not list or len(data['receipts']) > 3:
            raise gate.Invalid('invalid receipt collection')
        seen = set()
        for receipt in data['receipts']:
            Receipt(receipt)
            if receipt['domain'] in seen:
                raise gate.Invalid('duplicate domain')
            seen.add(receipt['domain'])


def build_policy(repository, target, actors, domains, pins, epoch=1):
    gate.exact(pins, gate.PINS)
    return Policy(dict(version=1, repository=repository, target=target,
                       actors=list(actors), domains=domains, epoch=epoch, **pins))


def load_policy(path, expected_digest=None):
    """Load controller-owned policy; an optional digest rejects content drift."""
    policy = Policy(Path(path).read_bytes())
    if expected_digest is not None and policy.digest != expected_digest:
        raise gate.Invalid('policy mismatch')
    return policy


def build_manifest(policy, base, candidate, tree, request, actor):
    policy = Policy(policy)
    p = policy.to_dict()
    return Manifest(dict(version=1, base=base, candidate=candidate, tree=tree,
                         request=request, actor=actor, policy=policy.digest,
                         **{k: p[k] for k in ('repository', 'target', 'epoch', *gate.PINS)}))


def build_bundle(manifest, receipts=()):
    return Bundle(dict(manifest=Manifest(manifest).to_dict(),
                       receipts=[Receipt(r).to_dict() for r in receipts]))


_CODES = {'stale evidence': 'EVIDENCE_STALE',
          'invalid evidence authentication': 'EVIDENCE_AUTHENTICATION',
          'missing or altered artifact': 'ARTIFACT_INVALID',
          'failed obligation': 'OBLIGATION_FAILED',
          'policy mismatch': 'POLICY_MISMATCH',
          'unauthorized actor': 'ACTOR_UNAUTHORIZED',
          'authority or evaluation context mismatch': 'CONTEXT_MISMATCH',
          'wrong producer or evidence kind': 'EVIDENCE_POLICY_MISMATCH',
          'required evidence unresolved': 'EVIDENCE_PENDING'}


def evaluate(bundle, policy, keys, artifacts):
    b, p = _value(bundle), _value(policy)
    result = gate.decide(b, p, keys, artifacts)
    result['code'] = ('ADMITTED' if result['verdict'] == 'ACCEPTED' else
                      _CODES.get(result.get('reason'), 'INPUT_INVALID'))
    result.setdefault('reason', 'all required evidence authenticated')
    result['field'] = {
        'EVIDENCE_STALE': 'receipts[].manifest',
        'EVIDENCE_AUTHENTICATION': 'receipts[].mac',
        'ARTIFACT_INVALID': 'receipts[].artifact',
        'OBLIGATION_FAILED': 'receipts[].status',
        'POLICY_MISMATCH': 'manifest.policy',
        'ACTOR_UNAUTHORIZED': 'manifest.actor',
        'CONTEXT_MISMATCH': 'manifest',
        'EVIDENCE_POLICY_MISMATCH': 'receipts[]',
        'EVIDENCE_PENDING': 'receipts',
    }.get(result['code'])
    domains = {}
    for domain in gate.DOMAINS:
        # Reuse the existing validator on one receipt. Its pending result means
        # this receipt was authenticated, but the other domains are absent.
        receipts = [r for r in b.get('receipts', []) if isinstance(r, dict) and r.get('domain') == domain] if isinstance(b, dict) and isinstance(b.get('receipts'), list) else []
        partial = gate.decide({'manifest': b.get('manifest'), 'receipts': receipts}, p, keys, artifacts) if isinstance(b, dict) else {'verdict': 'REJECTED'}
        domains[domain] = ('FAIL' if partial.get('reason') == 'failed obligation' else
                           'INVALID' if partial['verdict'] == 'REJECTED' else
                           receipts[0]['status'] if receipts else 'MISSING')
    result['domains'] = domains
    return result


def inspect_manifest(manifest):
    m = Manifest(manifest)
    return {'digest': m.digest, 'manifest': m.to_dict(), 'evidence_scope': 'local SHA-1 bare Git; trusted controller and producers'}


def diff_manifests(left, right):
    a, b = Manifest(left).to_dict(), Manifest(right).to_dict()
    return {key: {'before': a[key], 'after': b[key]} for key in sorted(a) if a[key] != b[key]}


def dry_run(bundle, policy, keys, artifacts):
    result = evaluate(bundle, policy, keys, artifacts)
    result['mutated'] = False
    if result['verdict'] == 'ACCEPTED':
        m = _value(bundle)['manifest']
        result['planned_updates'] = [{'ref': m['target'], 'expected': m['base'], 'new': m['candidate']},
                                     {'ref': 'refs/admission/consumed/' + gate.sha(m['request'].encode('ascii')), 'expected': None, 'new': m['candidate']}]
    return result


def reconcile(repo, request, manifest):
    """Read-only observation under trusted repository ownership, not a retry grant.

    Ref reads are not an atomic snapshot. Matching markers support historical
    commitment; absent markers never establish that an in-flight writer stopped.
    """
    m = Manifest(manifest).to_dict()
    if request != m['request']:
        return {'verdict': 'CONFLICT', 'code': 'REQUEST_MISMATCH'}
    try:
        if gate.git(repo, 'rev-parse', '--is-bare-repository') != 'true':
            return {'verdict': 'UNRESOLVED', 'code': 'REPOSITORY_UNSUPPORTED'}
        gate.git(repo, 'check-ref-format', m['target'])
        def read(ref):
            try:
                gate.git(repo, 'symbolic-ref', '-q', ref)
            except subprocess.CalledProcessError as error:
                if error.returncode != 1:
                    raise
            else:
                raise gate.Invalid('symbolic ref')
            try:
                return gate.git(repo, 'rev-parse', '--verify', '--quiet', ref)
            except subprocess.CalledProcessError as error:
                if error.returncode == 1:
                    return None
                raise
        marker = read('refs/admission/consumed/' + gate.sha(request.encode('ascii')))
        target = read(m['target'])
        if marker == m['candidate']:
            verdict, code = 'COMMITTED', 'COMMIT_OBSERVED'
        elif marker is not None:
            verdict, code = 'CONFLICT', 'REQUEST_CONSUMED'
        elif target == m['base']:
            verdict, code = 'UNRESOLVED', 'NOT_COMMITTED_OBSERVED'
        else:
            verdict, code = 'UNRESOLVED', 'COMMIT_OUTCOME_UNRESOLVED'
        return dict(verdict=verdict, code=code, target=target, consumed=marker, retry_authorized=False)
    except (OSError, subprocess.SubprocessError, gate.Invalid) as error:
        return {'verdict': 'UNRESOLVED', 'code': 'RECONCILIATION_FAILED', 'reason': str(error), 'retry_authorized': False}


def _bounded_command(command, cwd, timeout, output_limit):
    """POSIX process-group cleanup; descendants escaping the group need a sandbox."""
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    timed_out = truncated = False
    with subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          stdin=subprocess.DEVNULL, start_new_session=True, shell=False) as process:
        try:
            deadline = time.monotonic() + timeout
            with selectors.DefaultSelector() as selector:
                for name, stream in (('stdout', process.stdout), ('stderr', process.stderr)):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ, name)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        timed_out = True
                        break
                    for key, _ in selector.select(min(remaining, .05)):
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        buffer = buffers[key.data]
                        available = output_limit - len(buffer)
                        buffer.extend(chunk[:available])
                        if len(chunk) > available:
                            truncated = True
                            break
                    if truncated:
                        break
            if not (timed_out or truncated):
                try:
                    process.wait(timeout=max(.001, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    timed_out = True
        finally:
            # Also remove background descendants after the leader exits.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    return bytes(buffers['stdout']), bytes(buffers['stderr']), process.returncode, timed_out, truncated


def produce(manifest, policy, domain, command, keys, *, controller_authorized=False, cwd=None, timeout=30, output_limit=1048576):
    """Run trusted POSIX argv with a byte cap per stream; partial results stay pending."""
    if controller_authorized is not True:
        raise gate.Invalid('controller authorization required')
    m, p = Manifest(manifest), Policy(policy)
    gate.validate_policy(p.to_dict(), keys)
    context = gate.decide(build_bundle(m).to_dict(), p.to_dict(), keys, {})
    if context['verdict'] != 'PENDING':
        raise gate.Invalid(context.get('reason', 'invalid context'))
    rule = p.to_dict()['domains'].get(domain)
    if rule is None or rule['kind'] != 'bounded-test':
        raise gate.Invalid('generic commands produce bounded-test evidence only')
    if type(command) not in (list, tuple) or not command or any(type(x) is not str or not x or '\x00' in x for x in command):
        raise gate.Invalid('command must be explicit nonempty argv')
    if type(timeout) not in (int, float) or not 0 < timeout <= 300:
        raise gate.Invalid('timeout must be within 0 and 300 seconds')
    if os.name != 'posix':
        raise gate.Invalid('bounded producer requires POSIX process groups')
    if type(output_limit) is not int or not 1 <= output_limit <= 16777216:
        raise gate.Invalid('output_limit must be 1 to 16777216 bytes per stream')
    timed_out = truncated = False
    try:
        stdout, stderr, code, timed_out, truncated = _bounded_command(command, cwd, timeout, output_limit)
        status = 'PENDING' if timed_out or truncated else 'PASS' if code == 0 else 'FAIL'
    except OSError as error:
        status, stdout, stderr, code = 'PENDING', b'', str(error).encode()[:output_limit], None
    artifact = gate.canonical(dict(command=list(command), cwd=str(Path(cwd or '.').resolve()),
                                   timeout=timeout, returncode=code, status=status,
                                   output_limit_per_stream=output_limit, timed_out=timed_out, truncated=truncated,
                                   stdout_base64=base64.b64encode(stdout).decode(),
                                   stderr_base64=base64.b64encode(stderr).decode(), evidence_kind='bounded-test'))
    payload = dict(domain=domain, **rule, manifest=m.digest, artifact=gate.sha(artifact), status=status)
    payload['mac'] = hmac.digest(keys[rule['producer']], gate.canonical(payload), 'sha256').hex()
    return Receipt(payload), artifact


def demo():
    """Disposable real-Git example. Lost acknowledgement is simulated by omission."""
    with tempfile.TemporaryDirectory(prefix='admission-demo-') as directory:
        repo = Path(directory) / 'repo.git'
        subprocess.run(['git', 'init', '--bare', str(repo)], capture_output=True, check=True)
        gate.git(repo, 'config', 'user.name', 'Admission demo')
        gate.git(repo, 'config', 'user.email', 'demo@example.invalid')
        tree = gate.git(repo, 'mktree', input='')
        base = gate.git(repo, 'commit-tree', tree, input='base\n')
        candidate = gate.git(repo, 'commit-tree', tree, '-p', base, input='candidate\n')
        gate.git(repo, 'update-ref', 'refs/heads/main', base)
        domains = {d: dict(producer='checker-' + d, kind='bounded-test') for d in gate.DOMAINS}
        keys = {r['producer']: bytes([i + 1]) * 32 for i, r in enumerate(domains.values())}
        policy = build_policy('demo/repo', 'refs/heads/main', ['worker'], domains, {p: gate.sha(p.encode()) for p in gate.PINS})
        manifest = build_manifest(policy, base, candidate, tree, 'demo-request', 'worker')
        artifacts, receipts = {}, []
        for domain in gate.DOMAINS:
            receipt, data = produce(manifest, policy, domain, [sys.executable, '-c', 'print("demo check")'], keys, controller_authorized=True)
            artifacts[receipt.to_dict()['artifact']] = data
            receipts.append(receipt)
        bundle = build_bundle(manifest, receipts)
        pending = evaluate(build_bundle(manifest), policy, keys, artifacts)
        failed, data = produce(manifest, policy, 'behavior', [sys.executable, '-c', 'raise SystemExit(1)'], keys, controller_authorized=True)
        artifacts[failed.to_dict()['artifact']] = data
        rejected = evaluate(build_bundle(manifest, [failed, *receipts[1:]]), policy, keys, artifacts)
        plan = dry_run(bundle, policy, keys, artifacts)
        before = reconcile(repo, 'demo-request', manifest)
        committed = gate.execute(repo, 'demo/repo', bundle.to_dict(), policy.to_dict(), keys, artifacts)
        # Do not depend on the returned acknowledgement when reconciling.
        reconciled = reconcile(repo, 'demo-request', manifest)
        replay = gate.execute(repo, 'demo/repo', bundle.to_dict(), policy.to_dict(), keys, artifacts)
        return dict(pass_case=evaluate(bundle, policy, keys, artifacts), fail_case=rejected,
                    pending_case=pending, dry_run=plan, before=before, committed=committed,
                    lost_ack_reconciliation=reconciled, replay=replay,
                    limitations=['Disposable demo keys only', 'No sandbox or host enforcement', 'Lost acknowledgement simulated; no crash durability claim'])
