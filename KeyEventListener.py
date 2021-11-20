import copy

class KeyEventListener:
    def __init__(self):
        self.explicit_key_press_listeners = []
        self.explicit_key_release_listeners = []
        self.key_combo_listeners = []
        self.current_keys = []

    def subscribe_to_press_event(self, callback, keyfilter=None):
        registry = {
            'callback': callback,
            'filter': keyfilter
        }
        self.explicit_key_press_listeners.append(registry)

    def subscribe_to_combo_event(self, callback, key_combo_filter):
        registry = {
            'callback': callback,
            'filter': key_combo_filter
        }
        self.key_combo_listeners.append(registry)

    def raise_explicit_press_event(self, key, params={}, ignore=False):
        # print(key)

        if not ignore:
            self.current_keys.append(key)

        for listener in self.explicit_key_press_listeners:
            if listener['filter'] is not None:
                if key in listener['filter']:
                    listener['callback'](key, params)
            else:
                listener['callback'](key, params)

        if len(self.current_keys) > 1:
            self.raise_key_combo_event()

    def raise_explicit_release_event(self, key, params={}):
        self.current_keys.remove(key)

        for listener in self.explicit_key_release_listeners:
            if listener['filter'] is not None:
                if key in listener['filter']:
                    listener['callback'](key, params)
            else:
                listener['callback'](key, params)

    def raise_key_combo_event(self):
        for listener in self.key_combo_listeners:
            if set(listener['filter']) == set(self.current_keys):
                listener['callback']()

