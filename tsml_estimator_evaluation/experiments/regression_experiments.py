# -*- coding: utf-8 -*-
"""Classifier Experiments: code to run experiments as an alternative to orchestration.

This file is configured for runs of the main method with command line arguments, or for
single debugging runs. Results are written in a standard format. It is cloned from
classification_experiments, we should condense it all to one.
"""

__author__ = ["TonyBagnall"]

import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
import sklearn.utils
from classification_experiments import results_present
from sklearn.metrics import mean_squared_error
from sktime.datasets import load_from_tsfile_to_dataframe as load_ts
from sktime.datasets import write_results_to_uea_format

from tsml_estimator_evaluation.experiments.set_regressor import set_regressor


def resample(trainx, trainy, testx, testy, random_state):
    """Stratified resample data without replacement using a random state.

    Reproducable resampling. Combines train and test, resamples to get the same class
    distribution, then returns new train and test.

    Parameters
    ----------
    trainx : pd.DataFrame
        train data attributes in sktime pandas format.
    trainy : np.array
        train data class labels.
    testx : pd.DataFrame
        test data attributes in sktime pandas format.
    testy : np.array
        test data class labels as np array.
    random_state : int
        seed to enable reproducable resamples
    Returns
    -------
    new train and test attributes and class labels.
    """
    all_targets = np.concatenate((trainy, testy), axis=None)
    all_data = pd.concat([trainx, testx])
    random_state = sklearn.utils.check_random_state(random_state)
    train_cases = trainy.size
    test_cases = testy.size

    all_data["target"] = all_targets
    shuffled = all_data.sample(frac=1, random_state=1)
    # extract and remove the target column
    all_targets = shuffled["target"].to_numpy()
    shuffled = shuffled.drop("target", axis=1)
    # split the shuffled data into train and test
    trainx = shuffled.iloc[:train_cases]
    testx = shuffled.iloc[train_cases:]
    trainy = all_targets[:train_cases]
    testy = all_targets[train_cases:]
    # reset indexes to conform to sktime format.
    trainx = trainx.reset_index(drop=True)
    testx = testx.reset_index(drop=True)
    return trainx, trainy, testx, testy


def run_regression_experiment(
    X_train,
    y_train,
    X_test,
    y_test,
    regressor,
    results_path,
    regressor_name="",
    dataset="",
    resample_id=0,
):
    """Run a regression experiment and save the results to file.

    Method to run a basic experiment and write the results to files called
    testFold<resampleID>.csv and, if required, trainFold<resampleID>.csv.

    Parameters
    ----------
    X_train : pd.DataFrame or np.array
        The data to train the classifier.
    y_train : np.array, default = None
        Training data class labels.
    X_test : pd.DataFrame or np.array, default = None
        The data used to test the trained classifier.
    y_test : np.array, default = None
        Testing data class labels.
    regressor : BaseRegressor
        Regressor to be used in the experiment.
    results_path : str
        Location of where to write results. Any required directories will be created.
    regressor_name : str, default=""
        Name of the Regressor to use in file writing.
    dataset : str, default=""
        Name of problem to use in file writing.
    resample_id : int, default=0
        Seed for resampling. If set to 0, the default train/test split from file is
        used. Also used in output file name.
    """
    start = int(round(time.time() * 1000))
    regressor.fit(X_train, y_train)
    build_time = int(round(time.time() * 1000)) - start
    start = int(round(time.time() * 1000))
    preds = regressor.predict(X_test)
    test_time = int(round(time.time() * 1000)) - start
    second = str(regressor.get_params())
    second.replace("\n", " ")
    second.replace("\r", " ")
    mse = mean_squared_error(y_test, preds)
    third = f"{mse},{build_time},{test_time},-1,-1,,-1,-1"
    write_results_to_uea_format(
        second_line=second,
        third_line=third,
        first_line_comment="Generated by regression_experiments.py on "
        + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        timing_type="MILLISECONDS",
        output_path=results_path,
        estimator_name=regressor_name,
        resample_seed=resample_id,
        y_pred=preds,
        dataset_name=dataset,
        y_true=y_test,
        split="TEST",
        full_path=False,
    )


def load_and_run_regression_experiment(
    problem_path,
    results_path,
    dataset,
    regressor,
    resample_id=0,
    regressor_name=None,
    overwrite=False,
    predefined_resample=False,
):
    """Load a dataset and run a classification experiment.

    Method to run a basic experiment and write the results to files called
    testFold<resampleID>.csv and, if required, trainFold<resampleID>.csv.

    Parameters
    ----------
    problem_path : str
        Location of problem files, full path.
    results_path : str
        Location of where to write results. Any required directories will be created.
    dataset : str
        Name of problem. Files must be  <problem_path>/<dataset>/<dataset>+"_TRAIN.ts",
        same for "_TEST".
    regressor : BaseClassifier
        Classifier to be used in the experiment, if none is provided one is selected
        using cls_name using resample_id as a seed.
    regressor_name : str, default = None
        Name of classifier used in writing results. If none the name is taken from
        the classifier
    resample_id : int, default=0
        Seed for resampling. If set to 0, the default train/test split from file is
        used. Also used in output file name.
    overwrite : bool, default=False
        If set to False, this will only build results if there is not a result file
        already present. If True, it will overwrite anything already there.
    build_train : bool, default=False
        Whether to generate train files or not. If true, it performs a 10-fold
        cross-validation on the train data and saves. If the classifier can produce its
        own estimates, those are used instead.
    predefined_resample : bool, default=False
        Read a predefined resample from file instead of performing a resample. If True
        the file format must include the resample_id at the end of the dataset name i.e.
        <problem_path>/<dataset>/<dataset>+<resample_id>+"_TRAIN.ts".
    """
    if regressor_name is None:
        regressor_name = type(regressor).__name__
    # Check which files exist, if both exist, exit
    build_test = True
    if not overwrite:
        full_path = (
            f"{results_path}/{regressor_name}/Predictions/"
            f"{dataset}/testResample{resample_id}.csv"
        )
        if os.path.exists(full_path):
            build_test = False
        if build_test is False:
            return

    if predefined_resample:
        X_train, y_train = load_ts(
            problem_path + dataset + "/" + dataset + str(resample_id) + "_TRAIN.ts"
        )
        X_test, y_test = load_ts(
            problem_path + dataset + "/" + dataset + str(resample_id) + "_TEST.ts"
        )
    else:
        X_train, y_train = load_ts(problem_path + dataset + "/" + dataset + "_TRAIN.ts")
        X_test, y_test = load_ts(problem_path + dataset + "/" + dataset + "_TEST.ts")
        if resample_id != 0:
            X_train, y_train, X_test, y_test = resample(
                X_train, y_train, X_test, y_test, resample_id
            )
    y_train = y_train.astype(float)
    y_test = y_test.astype(float)
    run_regression_experiment(
        X_train,
        y_train,
        X_test,
        y_test,
        regressor,
        results_path,
        regressor_name=regressor_name,
        dataset=dataset,
        resample_id=resample_id,
    )


def run_experiment(args):
    if args.__len__() > 1:  # cluster run, this is fragile
        print(" Input args = ", sys.argv)
        data_dir = sys.argv[1]
        results_dir = sys.argv[2]
        regressor_name = sys.argv[3]
        dataset = sys.argv[4]
        resample = int(sys.argv[5]) - 1

        if len(sys.argv) > 6:
            tf = sys.argv[6].lower() == "true"
        else:
            tf = False

        if len(sys.argv) > 7:
            predefined_resample = sys.argv[7].lower() == "true"
        else:
            predefined_resample = False
        # this is also checked in load_and_run, but doing a quick check here so can
        # print a message and make sure data is not loaded
        if results_present(results_dir, regressor_name, dataset, resample):
            print("Ignoring, results already present")
        else:
            load_and_run_regression_experiment(
                problem_path=data_dir,
                results_path=results_dir,
                regressor=set_regressor(regressor_name, resample, tf),
                regressor_name=regressor_name,
                dataset=dataset,
                resample_id=resample,
                predefined_resample=predefined_resample,
            )
    else:  # Local run, just hack it
        print(" Local Run of TimeSeriesForestRegressor")
        data_dir = "C://Data/"
        results_dir = "C://Temp/"
        regressor_name = "TimeSeriesForestRegressor"
        n_jobs = 1
        regressor = set_regressor(regressor_name, n_jobs=n_jobs)
        dataset = "Covid3Month"
        resample = 0
        tf = False
        predefined_resample = False

        load_and_run_regression_experiment(
            overwrite=True,
            problem_path=data_dir,
            results_path=results_dir,
            regressor_name=regressor_name,
            regressor=regressor,
            dataset=dataset,
            resample_id=resample,
            predefined_resample=predefined_resample,
        )


if __name__ == "__main__":
    """
    Example simple usage, with arguments input via script or hard coded for testing.
    """
    run_experiment(sys.argv)
