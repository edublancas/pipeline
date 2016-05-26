# Pipeline project

WIP. A lot of things will change.

## Basic example

```python
# create pipeline object and pass configuration dictionaries
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
```

The following example will  generate a JSON output ([see example](output-example/readme.json)) with relevant information (model type, parameters, feature importances, training time, etc.) automatically and will also print relevant information using the Python `logging` module ([see example](output-example/readme.log)).
