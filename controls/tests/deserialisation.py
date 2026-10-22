# Fixtures for controls/rules/deserialisation.yaml
#
# STEAL: IGNORE: Deliberately vulnerable by design. The `ruleid:` cases below execute
# arbitrary code on untrusted input — pickle, marshal, unsafe YAML, pickled model loading.
# They exist to be caught, never to be copied.
#
# Run with: semgrep --test --config controls/rules controls/tests

import json
import marshal
import pickle

import joblib
import torch
import yaml


def unsafe_pickle(blob, fh):
    # ruleid: runwai-python-unsafe-pickle
    pickle.loads(blob)

    # ruleid: runwai-python-unsafe-pickle
    pickle.load(fh)

    # ruleid: runwai-python-unsafe-pickle
    marshal.loads(blob)


def safe_data_format(blob):
    # ok: runwai-python-unsafe-pickle
    json.loads(blob)


def unsafe_yaml(text):
    # ruleid: runwai-python-unsafe-yaml
    yaml.load(text)

    # FullLoader still constructs arbitrary Python objects for some tags.
    # ruleid: runwai-python-unsafe-yaml
    yaml.load(text, Loader=yaml.FullLoader)

    # ruleid: runwai-python-unsafe-yaml
    yaml.unsafe_load(text)


def safe_yaml(text):
    # ok: runwai-python-unsafe-yaml
    yaml.safe_load(text)

    # ok: runwai-python-unsafe-yaml
    yaml.load(text, Loader=yaml.SafeLoader)


def unsafe_model_load(path):
    # ruleid: runwai-python-model-pickle-load
    torch.load(path)

    # ruleid: runwai-python-model-pickle-load
    joblib.load(path)

    # Saying the unsafe part out loud does not make it safe.
    # ruleid: runwai-python-model-pickle-load
    torch.load(path, weights_only=False)


def safer_model_load(path):
    # weights_only=True refuses to unpickle arbitrary objects.
    # ok: runwai-python-model-pickle-load
    torch.load(path, weights_only=True)
