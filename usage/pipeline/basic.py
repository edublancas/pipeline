from pipeline import SKPipeline
from pipeline.lab.util import top_k

from dstools.util import config
from dstools.util import load_yaml
from dstools.sklearn import grid_generator

from sklearn.datasets import load_iris
from sklearn.metrics import precision_score
from sklearn.cross_validation import train_test_split
import logging

# logger configuration
log = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

# create pipeline object
pip = SKPipeline(config, load_yaml('exp.yaml'), workers=1)


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


# this function is called on every iteration, it must return an unfitted
# model
@pip.model_iterator
def model_iterator(config):
    classes = ['sklearn.ensemble.RandomForestClassifier',
               'sklearn.ensemble.AdaBoostClassifier']
    models = grid_generator.grid_from_classes(classes)
    return models


# function used to train models, must return a fitted model
@pip.train
def train(config, model, data, record):
    model.fit(data['X_train'], data['y_train'])
    preds = model.predict(data['X_test'])

    record['precision'] = precision_score(data['y_test'], preds)
    return model


# optional function run when every model has been trained
@pip.finalize
def finalize(config, experiment):
    pass
    # experiment.records = top_k(experiment.records, 'precision', 4)


# run pipeline
pip()
