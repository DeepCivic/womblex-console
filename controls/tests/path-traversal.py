# Fixtures for controls/rules/path-traversal.yaml
#
# STEAL: IGNORE: Deliberately vulnerable by design. Every `ruleid:` line below is a working
# path traversal that exists so a rule can be asserted against it. Lifting any of it into
# real code ships the exact defect the rule beside it was written to catch.
#
# Run with: semgrep --test --config controls/rules controls/tests
# `ruleid:` asserts the rule fires on the next line. `ok:` asserts it does not.
# The `ok:` cases are the point: a rule that cannot distinguish a caller-supplied segment
# from a literal path is not a control, it is noise.

import os
import pathlib
import shutil
from pathlib import Path

BASE = "/srv/app/data"


def read_by_interpolation(name):
    # ruleid: runwai-python-path-traversal-sink
    with open(f"/srv/app/data/{name}") as fh:
        return fh.read()


def read_by_concatenation(name):
    # ruleid: runwai-python-path-traversal-sink
    return open("/srv/app/data/" + name).read()


def read_by_percent_format(name):
    # ruleid: runwai-python-path-traversal-sink
    return open("/srv/app/data/%s" % name).read()


def read_by_str_format(name):
    # ruleid: runwai-python-path-traversal-sink
    return open("/srv/app/data/{}".format(name)).read()


def delete_by_interpolation(name):
    # ruleid: runwai-python-path-traversal-sink
    os.remove(f"/tmp/uploads/{name}")


def wipe_by_interpolation(name):
    # ruleid: runwai-python-path-traversal-sink
    shutil.rmtree(f"/tmp/workspaces/{name}")


def path_object_by_interpolation(name):
    # ruleid: runwai-python-path-traversal-sink
    return pathlib.Path(f"/srv/app/data/{name}")


def read_static_path():
    # A literal path carries no caller-supplied segment.
    # ok: runwai-python-path-traversal-sink
    return open("/etc/hostname").read()


def read_from_variable_already_checked(safe_path):
    # The value arrives as a whole, not assembled here. Sink matching is about the shape
    # of the assembly, so this is out of scope rather than approved — see the rule header.
    # ok: runwai-python-path-traversal-sink
    return open(safe_path).read()


def join_then_open(name):
    # ruleid: runwai-python-path-join-unresolved
    return open(os.path.join(BASE, name)).read()


def join_then_open_with_mode(name):
    # ruleid: runwai-python-path-join-unresolved
    return open(os.path.join(BASE, name), "rb").read()


def join_then_delete(name):
    # ruleid: runwai-python-path-join-unresolved
    os.remove(os.path.join(BASE, name))


def pathlib_joinpath_then_open(name):
    # ruleid: runwai-python-path-join-unresolved
    return Path(BASE).joinpath(name).open().read()


def pathlib_divide_then_read(name):
    # ruleid: runwai-python-path-join-unresolved
    return (Path(BASE) / name).read_text()


def join_of_literals_is_fine():
    # Both segments are literals, so nothing a caller supplies reaches the sink.
    # ok: runwai-python-path-join-unresolved
    return open(os.path.join("/srv/app/data", "schema.json")).read()


def canonicalised_before_open(name):
    # realpath at the sink is what the rule asks for. Whether the caller then compares the
    # result to the base is not something a sink match can see, and the rule header says so.
    # ok: runwai-python-path-join-unresolved
    return open(os.path.realpath(os.path.join(BASE, name))).read()
