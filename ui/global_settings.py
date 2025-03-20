# if Scene settings is not enough global

import bpy


class GlobalSettings:
    setting_name = None
    default = 0

    def __init__(self, setting_name, default=0):
        self.setting_name = setting_name
        self.default = default

    def _get_obj(self):
        name = 'audvis_global_settings'
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
        else:
            obj = bpy.data.objects.new(name, None)
            # obj.use_fake_user = True  # TODO
        return obj

    def get(self, audvis_settings):
        obj = self._get_obj()
        if self.setting_name in obj:
            return obj[self.setting_name]
        return 0

    def set(self, audvis_settings, value):
        self._get_obj()[self.setting_name] = value

    def getter(self):  # override "TypeError: get keyword: expected a function type, not a method"
        def anon(audvis_settings):
            return self.get(audvis_settings)

        return anon

    def setter(self):  # override "TypeError: set keyword: expected a function type, not a method"
        def anon(audvis_settings, value):
            return self.set(audvis_settings, value)

        return anon
