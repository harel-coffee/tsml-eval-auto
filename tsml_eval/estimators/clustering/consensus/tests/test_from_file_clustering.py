import os
from pathlib import Path

import numpy as np
from aeon.datasets import load_arrow_head
from sklearn.metrics import rand_score

from tsml_eval.estimators.clustering.consensus.ivc_from_file import \
    FromFileIterativeVotingClustering
from tsml_eval.estimators.clustering.consensus.simple_vote_from_file import \
    FromFileSimpleVote


_TEST_RESULTS_PATH = os.path.dirname(Path(__file__).parent.parent.parent.parent.parent) + "/tsml_eval/estimators/clustering/consensus/tests/test_files/"


def test_from_file_simple_vote():
    """Test SimpleVote from file with ArrowHead results."""
    X_train, y_train = load_arrow_head(split="train")
    X_test, y_test = load_arrow_head(split="test")

    file_paths = [
        _TEST_RESULTS_PATH + "/ArrowHead/PAM-DTW/",
        _TEST_RESULTS_PATH + "/ArrowHead/PAM-ERP/",
        _TEST_RESULTS_PATH + "/ArrowHead/PAM-MSM/",
    ]

    sv = FromFileSimpleVote(clusterers=file_paths, n_clusters=3, random_state=0)
    sv.fit(X_train, y_train)
    preds = sv.predict(X_test)

    assert sv.labels_.shape == (len(X_train),)
    assert isinstance(sv.labels_, np.ndarray)
    assert rand_score(y_train, sv.labels_) >= 0.6
    assert preds.shape == (len(X_test),)
    assert isinstance(preds, np.ndarray)
    assert rand_score(y_test, preds) >= 0.6


def test_from_file_iterative_voting_clustering():
    """Test SimpleVote from file with ArrowHead results."""
    X_train, y_train = load_arrow_head(split="train")
    X_test, y_test = load_arrow_head(split="test")

    file_paths = [
        _TEST_RESULTS_PATH + "/ArrowHead/PAM-DTW/",
        _TEST_RESULTS_PATH + "/ArrowHead/PAM-ERP/",
        _TEST_RESULTS_PATH + "/ArrowHead/PAM-MSM/",
    ]

    ivc = FromFileIterativeVotingClustering(clusterers=file_paths, n_clusters=3, max_iterations=100, random_state=0)
    ivc.fit(X_train, y_train)
    preds = ivc.predict(X_test)

    assert ivc.labels_.shape == (len(X_train),)
    assert isinstance(ivc.labels_, np.ndarray)
    assert rand_score(y_train, ivc.labels_) >= 0.6
    assert preds.shape == (len(X_test),)
    assert isinstance(preds, np.ndarray)
    assert rand_score(y_test, preds) >= 0.6