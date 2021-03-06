import logging
import collections
from datetime import datetime

from .lab import Experiment, SKExperiment
from .util import hash_sha1_numpy_array, class_name
from .sklearn.util import model_name

log = logging.getLogger(__name__)
MAX_WORKERS = 20


class Pipeline(object):
    _ExperimentClass = Experiment

    def __init__(self, config, exp_config, workers=1, save=True,
                 hash_data=True):
        # if backend selected is TinyDB and workers>1, raise an exception
        # since TinyDB has no support for concurrent connections
        if exp_config['backend'] == 'tiny' and workers > 1:
            raise Exception(('You cannot run a pipeline with workers>1'
                             ' using TinyDB, since it does not have'
                             ' for concurrent connections. Use another'
                             ' backend.'))

        log.debug('Init with config: {}'.format(config))

        if workers > MAX_WORKERS:
            self._workers = MAX_WORKERS
            log.info('Max workers is {}.'.format(MAX_WORKERS))
        else:
            self._workers = workers

        self._save = save
        self._hash_data = hash_data
        self.config = config

        # initialize dict to save the data hashes
        self._data_hashes = {}

        # dict to keep track of user functions
        self._user_fns = {}

        # create experiment instance
        self.ex = self.__class__._ExperimentClass(**exp_config)

    # the following functions act just to register user-defined functions
    def load(self, fn):
        self._user_fns['load'] = fn
        return fn

    def model_iterator(self, fn):
        self._user_fns['model_iterator'] = fn
        return fn

    def train(self, fn):
        self._user_fns['train'] = fn
        return fn

    def finalize(self, fn):
        self._user_fns['finalize'] = fn
        return fn

    def _load(self):
        config = self.config.get('load')
        data = self._user_fns['load'](config)
        if isinstance(data, collections.Mapping):
            self.data = data
        else:
            raise TypeError(('Object returned from load method should be'
                             ' a Mapping class. e.g. dict'))

        # save the hash of the datasets if hash_data is True
        # although we are not saving it on the experiment instance
        # right now, is better to raise an exception early if something
        # goes wrong
        if self._hash_data:
            for k, v in self.data.items():
                log.info('Hashing {}'.format(k))
                try:
                    h = hash_sha1_numpy_array(v)
                except Exception, e:
                    raise e
                else:
                    key = '{}'.format(k)
                    self._data_hashes[key] = h

    def _model_iterator(self):
        config = self.config.get('model_iterator')
        log.debug('Model iterator config: {}'.format(config))

        return self._user_fns['model_iterator'](config)

    def _train(self, model, record):
        record['_model_class'] = class_name(model)
        config = self.config.get('train')
        self._user_fns['train'](config, model, self.data, record)

    def _finalize(self, experiment):
        # save config used for this experiment on all records
        self.ex['_config'] = self.config

        # save data hashes if needed
        if self._hash_data:
            self.ex['_data_sha1_hashes'] = self._data_hashes

        # run function if the user provided one
        if self._user_fns['finalize']:
            config = self.config.get('finalize')
            self._user_fns['finalize'](config, experiment)

        # get time now
        pipeline_ended = datetime.utcnow()
        # store start and end dates on all records
        self.ex['_experiment_start'] = self._pipeline_started
        self.ex['_experiment_end'] = pipeline_ended

    def __call__(self):
        # store the time when the execution started
        self._pipeline_started = datetime.utcnow()
        # first - check if all the functions needed exist
        if not all([self._user_fns['load'],
                    self._user_fns['model_iterator'],
                    self._user_fns['train']]):
            raise Exception(('You need to provide functions for load,'
                             ' model_iterator and train functions.'
                             ' One or more missing.'))

        log.info('Pipeline started. Loading data.')
        self._load()
        log.info('Data loaded. Starting models loop.')

        model_iterator = self._model_iterator()
        # see if self._model_iterator has len
        try:
            total = len(model_iterator)
        except:
            log.info('Number of models to train is unknown')
            total = None
        else:
            log.info('Models to train: {}'.format(total))

        if self._workers > 1:
            self._concurrent_run(model_iterator, total)
        else:
            self._serial_run(model_iterator, total)

        log.info('Running finalize step.')
        self._finalize(self.ex)

        if self._save:
            self.ex.save()

    def _serial_run(self, model_iterator, total):
        for i, model in enumerate(model_iterator, 1):
            self._one_step(model, i, total)

    def _concurrent_run(self, model_iterator, total):
        from concurrent import futures
        # maybe multiprocessing would be better for this
        with futures.ThreadPoolExecutor(self._workers) as executor:
            executor.map(self._one_step, model_iterator, range(1, total),
                         [total]*total)

    def _one_step(self, model, i, total):
        if total:
            log.info('{}/{} - Running with: {}'.format(i, total, model))
        else:
            log.info('{} - Running with: {}'.format(i, model))

        record = self.ex.record()

        start = datetime.utcnow()
        self._train(model, record)
        end = datetime.utcnow()
        # save training time in minutes
        record['_training_time_sec'] = (end - start).total_seconds()


class SKPipeline(Pipeline):
    '''
        Pipeline subclass. Provides enhanced functionality
        when using scikit-learn.
            - Automatically saves model name e.g. RandomForestClassifier
            - Saves model parameters via model.get_params()
            - Uses Record subclass SKRecord which provides a method
                for instantiating models based on db records
    '''
    _ExperimentClass = SKExperiment

    def _load(self):
        super(SKPipeline, self)._load()
        # check that the user added data with the appropiate keys
        # to later retrieve the hashes in the MetaEstimator,
        # if not, log a message
        if ('X_train' not in self.data) or ('y_train' not in self.data):
            log.info(("Both 'X_train' and 'y_train' must be present"
                      " in data to be able to retrieve models form the db."))

    def _train(self, model, record):
        super(SKPipeline, self)._train(model, record)
        # save scikit-learn model info
        record['_params'] = model.get_params()
        record['_model_name'] = model_name(model)
        # try to get feature importances
        try:
            record['_feature_importances'] = (model.feature_importances_.
                                              tolist())
        except:
            pass
        # try to get coefficients
        try:
            record['_coef'] = model.coef_.tolist()
        except:
            pass
