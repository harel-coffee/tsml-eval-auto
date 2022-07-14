# Simple usages for building classifiers

from sktime.classification.feature_based import FreshPRINCE
from sktime.classification.compose import ClassifierPipeline
from sktime.transformations.panel.catch22 import Catch22
from sktime.datasets import load_arrow_head
from sktime.datasets import load_UCR_UEA_dataset
from sktime_estimator_evaluation.evaluation import fetch_classifier_metric

import numpy as np

def basic_usage():
    arrow_X, arrow_y = load_arrow_head(return_type="numpy2d")
    # work directly with numpy 2D for equal length univariate
    # 10 series equal length of 50
    train_X = np.random.rand(10, 50)
    # 20 series equal length of 50
    test_X = np.random.rand(20, 50)
    # Random class labels
    train_Y =np.random.randint(0, high=2, size=10)
    test_Y =np.random.randint(0, high=2, size=20)
    freshPrince = FreshPRINCE()
    freshPrince.fit(train_X, train_Y)
    preds = freshPrince.predict(test_X)
    print("Univariate preds", preds)
    # work directly with numpy 3D for equal length univariate
    # series of 3 dimensions, equal length of 50
    train_X = np.random.rand(10, 3, 50)
    test_X = np.random.rand(20, 3, 50)
    freshPrince.fit(train_X, train_Y)
    preds = freshPrince.predict(test_X)
    print(" Multivariate preds ", preds)
    # Load default train/test splits from sktime/datasets/data
    arrow_train_X, arrow_train_y = load_arrow_head(split="train", return_type="numpy2d")
    arrow_test_X, arrow_test_y = load_arrow_head(split="test", return_type="numpy2d")
    freshPrince.fit(arrow_train_X, arrow_train_y)
    s = freshPrince.score(arrow_test_X, arrow_test_y)
    print(" Score  = ", s)

def ucr_datasets(classifier, examples):
    scores = np.zeros(len(examples))
    for i in range(0, len(examples)):
        train_X, train_y = load_UCR_UEA_dataset(examples[i], split="TRAIN")
        test_X, test_y = load_UCR_UEA_dataset(examples[i], split="TEST")
        classifier.fit(train_X, train_y)
        scores[i] = classifier.score(test_X, test_y)
        print(" problem ", examples[i], " accuracy = ",scores[i])
    return scores


examples = ["Chinatown", "ItalyPowerDemand"]
freshPrince = FreshPRINCE()
acc = ucr_datasets(freshPrince, examples)
others = ["HC2", "InceptionTime", "ROCKET"]
other_accs = fetch_classifier_metric(
    metrics=['ACC'],
    datasets=examples,
    classifiers=others,
    folds=1,
    summary_format=False,
    return_numpy=True
)
# print as a table

# Make your own Pipeline
#summarytStats = Catch22
#ClassifierPipeline p =
