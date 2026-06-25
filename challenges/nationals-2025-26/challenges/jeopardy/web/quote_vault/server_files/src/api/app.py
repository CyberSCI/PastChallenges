#!/usr/bin/env python3
"""ocr-rotator API.

Two surfaces, one GraphQL schema:

  Schema fields:
      quote(id: Int!)             — safe, parameterized
      quotes                      — safe, parameterized
      search(query, limit)        — safe, parameterized
      findQuote(filter: String!)  — VULNERABLE; vendor-only field

  POST /api/quotes         — public GraphQL endpoint. Standard
                             introspection works and reveals all four
                             fields (including findQuote). However a
                             validation rule rejects any document that
                             selects findQuote: "Field 'findQuote' is
                             not accessible from this endpoint." So the
                             field is visible but not callable here.

  GET  /api/quotes/<path>  — wraps the URL path into a GraphQL query
                             template and runs the same schema *without*
                             the validation rule. The only way to
                             actually call findQuote is to break out of
                             the implicit `quote(id: <PATH>)` template
                             via path injection and chain a new
                             top-level findQuote field.

GET on /api/quotes (no path) is not handled — Flask returns 405.
No GraphiQL playground is served.
"""

import os
import re
import sqlite3
import sys

from flask import Flask, jsonify, request
from ariadne import QueryType, gql, graphql_sync, make_executable_schema
from graphql import GraphQLError
from graphql.validation import ValidationRule

DB_PATH = "/data/current/db.sqlite"
LISTEN_HOST = os.environ.get("API_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("API_PORT", "5000"))

app = Flask(__name__)


def _open_db():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# GraphQL schema (Ariadne)
# ---------------------------------------------------------------------------

type_defs = gql("""
    type Query {
        quote(id: Int!): Quote
        quotes: [Quote!]!
        search(query: String!, limit: Int = 10): [Quote!]!
        findQuote(filter: String!): Quote
        flag: String!
    }

    type Quote {
        id: Int!
        value: String!
        author: Author!
    }

    type Author {
        name: String!
    }
""")

# Flag visible to anyone who runs introspection and notices the `flag` field.
GRAPHQL_FLAG = "Cybersci{graphql-discovered-by-introspection-9847}"

# HMAC flag — derivable purely from constants in /js/app.js, no server
# endpoint required. The player has to:
#   1. read /js/app.js and find both _bld (the HMAC key) and a sibling
#      obfuscated constant string that decodes to "qv-flag-hmac-redemption"
#   2. compute HMAC-SHA256(constant, key)[:16] = "e0a66803d1e633ff"
#   3. wrap it as "Cybersci{hmac-<value>}" and submit to scoring.
# The expected flag is documented here so the scoring system / organizers
# know what to accept; the server itself never mints or validates it.
#
#   FLAG = "Cybersci{hmac-e0a66803d1e633ff}"


# ---- resolvers (plain functions) ----

def resolve_quote(_, info, id):
    conn = _open_db()
    try:
        cur = conn.execute(
            "SELECT id, value, author FROM quotes WHERE id = ? AND public = 1",
            (id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "value": row[1], "author": {"name": row[2]}}
    finally:
        conn.close()


def resolve_quotes(_, info):
    conn = _open_db()
    try:
        cur = conn.execute(
            "SELECT id, value, author FROM quotes WHERE public = 1 ORDER BY id"
        )
        return [
            {"id": r[0], "value": r[1], "author": {"name": r[2]}}
            for r in cur
        ]
    finally:
        conn.close()


def resolve_search(_, info, query, limit=10):
    if not isinstance(limit, int):
        limit = 10
    if limit < 1:
        limit = 1
    if limit > 25:
        limit = 25
    conn = _open_db()
    try:
        cur = conn.execute(
            "SELECT id, value, author FROM quotes "
            "WHERE value LIKE ? AND public = 1 LIMIT ?",
            (f"%{query}%", limit),
        )
        return [
            {"id": r[0], "value": r[1], "author": {"name": r[2]}}
            for r in cur
        ]
    finally:
        conn.close()


def resolve_find_quote(_, info, filter):
    """Vulnerable resolver — only bound on the internal schema.

    The `filter` argument is interpolated into a `SELECT count(*) ...`
    query. Only the integer count is consumed (UNION rows beyond the
    first are ignored), so the response shape never carries
    attacker-controlled data — only a boolean-blind signal: a TRUE
    boolean in the WHERE makes the count >0 and we return a quote;
    FALSE makes count=0 and we return null.
    """
    conn = _open_db()
    try:
        count_sql = (
            f"SELECT count(*) FROM quotes WHERE id = {filter} AND public = 1"
        )
        try:
            row = conn.execute(count_sql).fetchone()
        except sqlite3.Error:
            return None
        try:
            n = int(row[0]) if row else 0
        except (TypeError, ValueError):
            return None
        if n <= 0:
            return None
        m = re.match(r"\d+", filter)
        if not m:
            return None
        safe_id = int(m.group(0))
        cur = conn.execute(
            "SELECT id, value, author FROM quotes WHERE id = ? AND public = 1",
            (safe_id,),
        )
        q_row = cur.fetchone()
        if not q_row:
            return None
        return {
            "id": q_row[0],
            "value": q_row[1],
            "author": {"name": q_row[2]},
        }
    finally:
        conn.close()


def resolve_flag(_, info):
    """Constant flag exposed via the `flag` GraphQL field. Visible to
    anyone who introspects the schema and decides to call it."""
    return GRAPHQL_FLAG


query = QueryType()
query.set_field("quote", resolve_quote)
query.set_field("quotes", resolve_quotes)
query.set_field("search", resolve_search)
query.set_field("findQuote", resolve_find_quote)
query.set_field("flag", resolve_flag)

schema = make_executable_schema(type_defs, query)


# ---- validation rule: block findQuote on the public POST endpoint -----------
#
# `findQuote` lives in the unified schema (so introspection reveals it), but
# documents that select it are rejected when this rule is in effect. Path-
# injected GETs run the same schema *without* the rule, so findQuote works
# there.

class NoFindQuoteRule(ValidationRule):
    def enter_field(self, node, *_args):
        if node.name.value == "findQuote":
            self.report_error(
                GraphQLError(
                    "Field 'findQuote' is not accessible from this endpoint.",
                    node,
                )
            )


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


@app.route("/api/quotes", methods=["POST"])
def graphql_post():
    """Public GraphQL endpoint. Runs against the unified schema with the
    NoFindQuoteRule attached, so introspection reveals findQuote but
    documents that select it are rejected.
    """
    data = request.get_json(silent=True) or {}
    success, result = graphql_sync(
        schema,
        data,
        context_value={"request": request},
        validation_rules=[NoFindQuoteRule],
    )
    return jsonify(result), 200 if success else 400


# Template the URL path is plugged into. Closing braces / subfields after
# the implicit `quote(id: <PATH>)` are appended after the user's input,
# so a player who provides their own closing `)` and chains a new
# top-level field gets that field appended into the same selection set.
_PATH_TEMPLATE_PREFIX = "{ quote(id: "
_PATH_TEMPLATE_SUFFIX = ") { id value author { name } } }"


@app.route("/api/quotes/<path:id_raw>", methods=["GET"])
def get_quote_via_path(id_raw):
    """The URL path is interpolated into a GraphQL query template and
    executed against the unified schema *without* the NoFindQuoteRule.
    So findQuote is reachable here — but only by breaking out of the
    implicit `quote(id: <PATH>)` template via path injection.
    """
    query_text = _PATH_TEMPLATE_PREFIX + id_raw + _PATH_TEMPLATE_SUFFIX
    success, result = graphql_sync(
        schema,
        {"query": query_text},
        context_value={"request": request},
    )
    return jsonify(result), 200 if success else 400


def main():
    try:
        from waitress import serve
    except ImportError:
        print("warning: waitress not available, falling back to Flask dev server",
              file=sys.stderr, flush=True)
        app.run(host=LISTEN_HOST, port=LISTEN_PORT, threaded=True)
        return
    serve(app, host=LISTEN_HOST, port=LISTEN_PORT, threads=8)


if __name__ == "__main__":
    main()
