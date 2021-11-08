from . import (
    spread_drivers_ui,
    menuitem,
)

classes = spread_drivers_ui.classes \
          + menuitem.classes


def register():
    menuitem.WM_MT_button_context.append(menuitem.menu_func)


def unregister():
    menuitem.WM_MT_button_context.remove(menuitem.menu_func)
