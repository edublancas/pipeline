import logging

from sklearn.datasets import load_iris
from sklearn.metrics import precision_score
from sklearn.cross_validation import train_test_split
from dstools.util import config
from dstools.util import load_yaml
from dstools.sklearn import grid_generator
from pipeline.lab.util import top_k
from pipeline import SKPipeline


# logger configuration
log = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)


# create pipeline object
pip = SKPipeline(config, load_yaml('exp.yaml'))


# this function should return the all the data used to train models
# as a dictionary. In subsequentent functions the data will be available in
# the 'data' parameter
@pip.load
def load(config):
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target,
                                                        test_size=0.30,
                                                        random_state=0)
    data = {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test
    }
    return data


# this function is called on every iteration, must return a model to train
@pip.model_iterator
def model_iterator(config):
    classes = ['sklearn.ensemble.RandomForestClassifier',
               'sklearn.ensemble.AdaBoostClassifier']
    models = grid_generator.grid_from_classes(classes)
    return models


# function used to train models returns the result of the operation
@pip.train
def train(config, model, data, record):
    model.fit(data['X_train'], data['y_train'])
    preds = model.predict(data['X_test'])

    record['precision'] = precision_score(data['y_test'], preds)
    return model


# optional function - use this to check results/decide what to store
# in the database
@pip.finalize
def finalize(config, experiment):
    # only store the top 4 models using precision as the metric
    experiment.records = top_k(experiment.records, 'precision', 4)


# run pipeline
pip()
