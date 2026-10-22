# Fixtures for controls/rules/injection.yaml
#
# STEAL: IGNORE: Deliberately vulnerable by design. Every `ruleid:` line below is a working
# injection that exists so a rule can be asserted against it. Lifting any of it into real
# code ships the exact defect the rule beside it was written to catch.
#
# Run with: semgrep --test --config controls/rules controls/tests
# `ruleid:` asserts the rule fires on the next line. `ok:` asserts it does not.
# The `ok:` cases are the point: a rule that cannot distinguish safe from unsafe
# is not a control, it is noise.

import os
import subprocess


def sql_sinks(cur, user_id):
    # ruleid: runwai-python-sql-string-building
    cur.execute(f"SELECT * FROM users WHERE id = {user_id}")

    # ruleid: runwai-python-sql-string-building
    cur.execute("SELECT * FROM users WHERE id = %s" % user_id)

    # ruleid: runwai-python-sql-string-building
    cur.execute("SELECT * FROM users WHERE name = " + user_id)

    # ruleid: runwai-python-sql-string-building
    cur.execute("SELECT * FROM users WHERE id = {}".format(user_id))

    # ruleid: runwai-python-sql-string-building
    cur.executemany(f"INSERT INTO t VALUES ({user_id})")


def sql_assembled_then_executed(cur, user_id):
    # ruleid: runwai-python-sql-string-building-indirect
    q = f"SELECT * FROM users WHERE id = {user_id}"
    cur.execute(q)


def sql_assembled_with_bound_params_still_interpolated(cur, table):
    # Binding one value does not fix the interpolated table name.
    # ruleid: runwai-python-sql-string-building-indirect
    q = f"SELECT * FROM {table} WHERE active = %s"
    cur.execute(q, (True,))


def sql_assembled_far_from_the_sink(cur, user_id):
    # ruleid: runwai-python-sql-string-building-indirect
    q = f"DELETE FROM sessions WHERE user_id = {user_id}"
    rows_before = cur.rowcount
    cur.execute(q)
    return rows_before


def sql_assembled_static(cur):
    # A query assembled without interpolation carries no untrusted data.
    # ok: runwai-python-sql-string-building-indirect
    q = "SELECT count(*) FROM users"
    cur.execute(q)


def sql_parameterised(cur, user_id):
    # ok: runwai-python-sql-string-building
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))

    # ok: runwai-python-sql-string-building
    cur.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})

    # A fully static query is safe regardless of how it is written.
    # ok: runwai-python-sql-string-building
    cur.execute("SELECT count(*) FROM users")


def shell_sinks(name):
    # ruleid: runwai-python-shell-injection
    os.system(f"echo {name}")

    # ruleid: runwai-python-shell-injection
    os.system("echo " + name)

    # ruleid: runwai-python-shell-injection
    subprocess.run(f"ls {name}", shell=True)


def shell_safe(name):
    # ok: runwai-python-shell-injection
    subprocess.run(["ls", name], shell=False)

    # ok: runwai-python-shell-injection
    subprocess.run(["echo", name])

    # A static command with no interpolation is not an injection.
    # ok: runwai-python-shell-injection
    os.system("uptime")
