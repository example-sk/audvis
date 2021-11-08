class Scripting:
    callbacks = {}

    def run(self, audvis):
        for i in self.callbacks:
            self.callbacks[i](audvis.driver)

    def register(self, name, callback):
        self.callbacks[name] = callback

    def reset(self):
        self.callbacks = {}


classes = []
