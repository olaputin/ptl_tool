import os
import yaml


class ConfigException(Exception):
    pass


class Configs(object):
    def __init__(self):
        app_path = os.path.dirname(os.path.realpath(__file__))
        self._defaults = {
            'APPLICATION_PATH': app_path,
            'LOG_PATH': os.path.join(app_path, 'log')
        }

        self._stop_words = ['FIX_IT']

        if not os.path.exists(self._defaults['LOG_PATH']):
            os.makedirs(self._defaults['LOG_PATH'])

        self.common_conf = None
        with open(os.path.join(app_path, 'default.yaml'), 'r') as default_conf:
            try:
                self.common_conf = yaml.load(default_conf)
            except yaml.YAMLError as exc:
                print(exc)

        conf_path = os.path.join(app_path, 'conf.yaml')
        if os.path.exists(conf_path):
            with open(conf_path, 'r') as conf_path:
                self._recursive_update(self.common_conf, yaml.load(conf_path))
        self._check_data(self.common_conf)

    def _update_consts(self, val):
        for k, rep in self._defaults.iteritems():
            q = '__%s__' % k
            if val.find(q) >= 0:
                val = val.replace(q, rep)
        return val

    def _recursive_update(self, base, updated):
        for k in updated:
            if k in base:
                if isinstance(updated[k], dict) and isinstance(base[k], dict):
                    self._recursive_update(base[k], updated[k])
                else:
                    base[k] = updated[k]
            else:
                base[k] = updated[k]

    def _check_data(self, data, key=None):
        if isinstance(data, dict):
            for key, val in data.items():
                data[key] = self._check_data(val, key)
        elif isinstance(data, list):
            for n in range(len(data)):
                data[n] = self._check_data(data[n], key)

        elif isinstance(data, str):
            data = self._update_consts(data, key)
        return data

    def _update_consts(self, val, key):
        for stop_word in self._stop_words:
            sw = '__%s__' % stop_word
            if val.find(sw) >= 0:
                raise ConfigException("Config is incorrect: key {} should be fixed".format(key))
        for k, rep in self._defaults.items():
            q = '__%s__' % k
            if val.find(q) >= 0:
                val = val.replace(q, rep)
        return val
