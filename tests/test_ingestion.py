# tests/test_ingestion.py
import json
from datetime import datetime
from typing import Annotated

import kuzu
import pytest

import backend.memory.ingestion.ingest_nodes as ing  
from backend.memory.db import edges as edges_mod
from backend.memory.db.datapoints import (
    Blocker, Class, DataPoint, Dedup, Directory, File, Function,
    ReasoningNode, Session,
)
from backend.memory.db.edges import (
    Edge, FileContainsFunction, DirectoryContainsFile,
)
from backend.memory.db.kuzu import REL_TABLES, init_kuzu  
from backend.exceptions import (
    EdgeIngestionError, MissingEndpointError, NodeIngestionError,
)
import backend.memory.db as db_pkg
import backend.memory.db.kuzu as kuzu_mod

@pytest.fixture
def conn(tmp_path, monkeypatch):
    db = kuzu.Database(str(tmp_path / "kuzu_db"))
    c = kuzu.Connection(db)
    monkeypatch.setattr(db_pkg, "get_kuzu_connection", lambda: c)
    monkeypatch.setattr(kuzu_mod, "get_kuzu_connection", lambda: c, raising=False)
    kuzu_mod.init_kuzu()
    assert c.execute("CALL show_tables() RETURN name;").has_next(), "schema not created on test conn"
    yield c

# ---------- fakes and fixtures ----------

class FakeMerge:
    def __init__(self, table):
        self.table = table

    def when_matched_update_all(self):
        return self

    def when_not_matched_insert_all(self):
        return self

    def execute(self, rows):
        if self.table.fail:
            raise RuntimeError("lancedb down")
        self.table.calls += 1
        for r in rows:
            self.table.rows[r["id"]] = r


class FakeTable:
    def __init__(self, fail=False):
        self.rows = {}
        self.calls = 0
        self.fail = fail

    def merge_insert(self, key):
        assert key == "id"
        return FakeMerge(self)


def fake_embed_texts(texts):
    return [[float(len(t)), 0.0, 1.0] for t in texts]


@pytest.fixture(autouse=True)
def patch_embedder(monkeypatch):
    monkeypatch.setattr(ing, "embed_texts", fake_embed_texts)





@pytest.fixture
def table():
    return FakeTable()


def count(conn, query, params=None):
    return conn.execute(query, params or {}).get_next()[0]


def make_function(name="f", file_path="a.py", **kw):
    return Function(name=name, file_path=file_path, repo_name="r", **kw)


def make_node(label, seed):
    return {
        "Directory": lambda: Directory(path=f"d{seed}", repo_name="r"),
        "File": lambda: File(path=f"f{seed}.py", language="python", repo_name="r"),
        "Class": lambda: Class(name=f"C{seed}", file_path="f.py"),
        "Function": lambda: Function(name=f"fn{seed}", file_path="f.py", repo_name="r"),
        "Session": lambda: Session(session_id=seed, timestamp=datetime(2026, 1, 1)),
        "ReasoningNode": lambda: ReasoningNode(session_id=seed, intent=f"i{seed}"),
        "Blocker": lambda: Blocker(description=f"b{seed}", created_in=seed),
    }[label]()


# ---------- pure helpers (no DB) ----------

def test_embeddable_fields_function():
    assert set(ing._get_embeddable_fields(Function)) == {"docstring", "body_summary"}


def test_embeddable_fields_none_for_file():
    assert ing._get_embeddable_fields(File) == []


def test_embedding_text_joins_fields_and_skips_none():
    fn = make_function(docstring="does x", body_summary=None)
    assert ing._build_embedding_text(fn) == "does x"
    fn2 = make_function(docstring="does x", body_summary="calls y")
    assert ing._build_embedding_text(fn2) == "does x\ncalls y"


def test_embedding_text_empty_for_node_without_embeddables():
    f = File(path="a.py", language="python", repo_name="r")
    assert ing._build_embedding_text(f) == ""


def test_serialize_properties_dict_becomes_json():
    fn = make_function(docstring="d")
    props = ing._serialize_properties(fn)
    assert isinstance(props["metadata"], str)
    assert json.loads(props["metadata"])["index_fields"][0] == "name"
    assert props["args"] == []  # lists stay lists


def test_id_is_deterministic_and_respects_explicit_id():
    assert make_function().id == make_function().id
    assert make_function(name="g").id != make_function().id
    assert Function(id="custom", name="f", file_path="a.py", repo_name="r").id == "custom"


@pytest.mark.xfail(strict=True, reason="id hashes only Dedup fields; repo_name is not one, so repos collide")
@pytest.mark.parametrize("build", [
    lambda repo: Function(name="f", file_path="a.py", repo_name=repo),
    lambda repo: File(path="a.py", language="python", repo_name=repo),
    lambda repo: Directory(path="src", repo_name=repo),
])
def test_ids_differ_across_repos(build):
    assert build("repo1").id != build("repo2").id


# ---------- ingest_node (single) ----------

def test_ingest_node_writes_graph_and_vector(conn, table):
    fn = make_function(docstring="does x")
    ing.ingest_node(conn, table, fn, lambda t: [1.0, 2.0, 3.0])
    assert count(conn, "MATCH (n:Function) RETURN count(n)") == 1
    assert table.rows[fn.id]["vector"] == [1.0, 2.0, 3.0]
    assert table.rows[fn.id]["node_type"] == "Function"


# ---------- ingest_nodes ----------

def test_ingest_nodes_writes_graph_and_vectors(conn, table):
    fn = make_function(docstring="does x")
    f = File(path="a.py", language="python", repo_name="r")
    ing.ingest_nodes(conn, table, [fn, f])
    assert count(conn, "MATCH (n:Function) RETURN count(n)") == 1
    assert count(conn, "MATCH (n:File) RETURN count(n)") == 1
    assert set(table.rows) == {fn.id}          # File has no embeddable text
    assert table.rows[fn.id]["text"] == "does x"


def test_ingest_nodes_is_idempotent(conn, table):
    fn = make_function(docstring="does x")
    ing.ingest_nodes(conn, table, [fn])
    ing.ingest_nodes(conn, table, [fn])
    assert count(conn, "MATCH (n:Function) RETURN count(n)") == 1
    assert len(table.rows) == 1


def test_reingest_updates_properties(conn, table):
    ing.ingest_nodes(conn, table, [make_function(access_count=1)])
    ing.ingest_nodes(conn, table, [make_function(access_count=5)])
    assert count(conn, "MATCH (n:Function) RETURN n.access_count") == 5


def test_metadata_roundtrips_as_json(conn, table):
    ing.ingest_nodes(conn, table, [make_function()])
    raw = conn.execute("MATCH (n:Function) RETURN n.metadata").get_next()[0]
    assert json.loads(raw) == {"index_fields": ["name", "file_path", "docstring", "body_summary"]}


def test_only_non_embeddable_nodes_skips_lancedb(conn, table):
    ing.ingest_nodes(conn, table, [File(path="a.py", language="python", repo_name="r")])
    assert table.calls == 0
    assert count(conn, "MATCH (n:File) RETURN count(n)") == 1


def test_empty_node_list_is_noop(conn, table):
    ing.ingest_nodes(conn, table, [])
    assert table.calls == 0


def test_duplicate_nodes_in_one_batch(conn, table):
    fn = make_function(docstring="does x")
    ing.ingest_nodes(conn, table, [fn, fn])
    assert count(conn, "MATCH (n:Function) RETURN count(n)") == 1
    # NOTE: this fake tolerates duplicate rows. Real LanceDB merge_insert can
    # reject duplicate source keys, so verify against a real table too.


class Ghost(DataPoint):
    name: Annotated[str, Dedup()]


def test_mid_batch_failure_rolls_back_graph(conn, table):
    good = make_function(docstring="does x")
    with pytest.raises(NodeIngestionError):
        ing.ingest_nodes(conn, table, [good, Ghost(name="no_table")])
    assert count(conn, "MATCH (n:Function) RETURN count(n)") == 0
    assert table.calls == 0  # LanceDB never touched after a graph failure


@pytest.mark.xfail(strict=True, reason="embed_texts runs outside the try block, raw error escapes")
def test_embedding_failure_is_wrapped(conn, table, monkeypatch):
    def boom(texts):
        raise RuntimeError("api down")
    monkeypatch.setattr(ing, "embed_texts", boom)
    with pytest.raises(NodeIngestionError):
        ing.ingest_nodes(conn, table, [make_function(docstring="d")])


@pytest.mark.xfail(strict=True, reason="graph commits before LanceDB write, no compensation on failure")
def test_lancedb_failure_does_not_leave_orphan_graph_nodes(conn):
    table = FakeTable(fail=True)
    with pytest.raises(NodeIngestionError):
        ing.ingest_nodes(conn, table, [make_function(docstring="d")])
    assert count(conn, "MATCH (n:Function) RETURN count(n)") == 0


# ---------- edges ----------

@pytest.fixture
def seeded(conn, table):
    d = Directory(path="src", repo_name="r")
    f = File(path="src/a.py", language="python", repo_name="r")
    fn = make_function(file_path="src/a.py")
    ing.ingest_nodes(conn, table, [d, f, fn])
    return d, f, fn


def test_ingest_edges_creates_edge(conn, seeded):
    _, f, fn = seeded
    ing.ingest_edges(conn, [FileContainsFunction.from_nodes(f, fn)])
    q = "MATCH (:File)-[r:FileContainsFunction]->(:Function) RETURN count(r)"
    assert count(conn, q) == 1


def test_ingest_edges_is_idempotent(conn, seeded):
    _, f, fn = seeded
    e = FileContainsFunction.from_nodes(f, fn)
    ing.ingest_edges(conn, [e])
    ing.ingest_edges(conn, [e])
    q = "MATCH (:File)-[r:FileContainsFunction]->(:Function) RETURN count(r)"
    assert count(conn, q) == 1


def test_ingest_edges_empty_list(conn):
    ing.ingest_edges(conn, [])


def test_missing_source_raises(conn, seeded):
    _, _, fn = seeded
    e = FileContainsFunction(source_id="nope", target_id=fn.id)
    with pytest.raises(MissingEndpointError):
        ing.ingest_edges(conn, [e])


def test_missing_target_raises(conn, seeded):
    _, f, _ = seeded
    e = FileContainsFunction(source_id=f.id, target_id="nope")
    with pytest.raises(MissingEndpointError):
        ing.ingest_edges(conn, [e])


def test_bad_edge_rolls_back_earlier_edges(conn, seeded):
    d, f, fn = seeded
    good = DirectoryContainsFile.from_nodes(d, f)
    bad = FileContainsFunction(source_id=f.id, target_id="nope")
    with pytest.raises(MissingEndpointError):
        ing.ingest_edges(conn, [good, bad])
    assert count(conn, "MATCH ()-[r:DirectoryContainsFile]->() RETURN count(r)") == 0


class Bogus(Edge):
    pass


def test_unknown_edge_type_is_wrapped(conn, seeded):
    _, f, fn = seeded
    with pytest.raises(EdgeIngestionError):
        ing.ingest_edges(conn, [Bogus(source_id=f.id, target_id=fn.id)])


@pytest.mark.xfail(strict=True, reason="ingest_edge silently creates nothing when an endpoint is missing")
def test_single_ingest_edge_raises_on_missing_endpoint(conn, seeded):
    _, f, _ = seeded
    with pytest.raises(MissingEndpointError):
        ing.ingest_edge(conn, FileContainsFunction(source_id=f.id, target_id="nope"))


def test_single_ingest_edge_happy_path(conn, seeded):
    _, f, fn = seeded
    ing.ingest_edge(conn, FileContainsFunction.from_nodes(f, fn))
    q = "MATCH (:File)-[r:FileContainsFunction]->(:Function) RETURN count(r)"
    assert count(conn, q) == 1


@pytest.mark.parametrize("rel", sorted(REL_TABLES))
def test_every_rel_table_entry_matches_schema(conn, table, rel):
    """Catches drift between REL_TABLES, the edge classes, and the Kuzu schema."""
    src_label, tgt_label = REL_TABLES[rel]
    src, tgt = make_node(src_label, 1), make_node(tgt_label, 2)
    ing.ingest_nodes(conn, table, [src, tgt])
    edge_cls = getattr(edges_mod, rel)
    ing.ingest_edges(conn, [edge_cls.from_nodes(src, tgt)])
    q = f"MATCH (:{src_label})-[r:{rel}]->(:{tgt_label}) RETURN count(r)"
    assert count(conn, q) == 1


# ---------- ingest_batch ----------

def test_ingest_batch_happy_path(conn, table):
    f = File(path="a.py", language="python", repo_name="r")
    fn = make_function(docstring="d")
    ing.ingest_batch(conn, table, [f, fn], [FileContainsFunction.from_nodes(f, fn)])
    assert count(conn, "MATCH ()-[r:FileContainsFunction]->() RETURN count(r)") == 1
    assert fn.id in table.rows


def test_ingest_batch_missing_endpoint_propagates(conn, table):
    f = File(path="a.py", language="python", repo_name="r")
    bad = FileContainsFunction(source_id=f.id, target_id="nope")
    with pytest.raises(MissingEndpointError):
        ing.ingest_batch(conn, table, [f], [bad])

def test_embedder_not_called_when_nothing_to_embed(conn, table, monkeypatch):
    def strict_embed(texts):
        assert texts, "embed_texts must not be called with an empty list"
        return [[0.0, 0.0, 1.0] for _ in texts]
    monkeypatch.setattr(ing, "embed_texts", strict_embed)

    ing.ingest_nodes(conn, table, [File(path="a.py", language="python", repo_name="r")])
    assert count(conn, "MATCH (n:File) RETURN count(n)") == 1
    assert table.calls == 0