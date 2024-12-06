"""Expose sensors as a Restful API"""
import json
import logging
import threading
import traceback

from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "RESTful"
        self.lnxlink = lnxlink
        self._requirements()

    def _requirements(self):
        flask_view = import_install_package("flask", ">=3.0.3", "flask.views")
        flask = import_install_package("flask", ">=3.0.3", "flask")

        class ModuleInfo(flask_view.views.MethodView):
            """Get information from Addon modules"""

            def __init__(self, lnxlink):
                """Init the application"""
                self.lnxlink = lnxlink

            def get(self, module=None):
                """Fetch data from modules"""
                info = self.lnxlink.saved_publish
                if module is None:
                    return json.dumps(list(info.keys()))
                return str(info.get(module))

        class ModuleControl(flask_view.views.MethodView):
            """Control Addon modules"""

            def __init__(self, lnxlink):
                """Init the application"""
                self.lnxlink = lnxlink

            def get(self):
                """Information about control modules"""
                modules = []
                for addonmodule, addon in self.lnxlink.addons.items():
                    if hasattr(addon, "start_control"):
                        modules.append(addonmodule)
                return json.dumps(modules)

            def post(self, module=None):
                """Control an Addon module"""
                if module is None:
                    modules = []
                    for addonmodule, addon in self.lnxlink.addons.items():
                        if hasattr(addon, "start_control"):
                            modules.append(addonmodule)
                    return json.dumps(modules)

                topic = flask.request.form.get("topic", "")
                topic = f"{module}/{topic}"
                topic = topic.split("/")
                message = flask.request.form.get("message")
                addon = self.lnxlink.addons.get(module)
                if addon is not None:
                    if hasattr(addon, "start_control"):
                        try:
                            result = addon.start_control(topic, message)
                            return json.dumps(result)
                        except Exception as err:
                            logger.error(
                                "Couldn't run command for module %s: %s, %s",
                                addon,
                                err,
                                traceback.format_exc(),
                            )
                            return f"Error: {err}"
                    return "No control support available"
                return "Module not found"

        app = flask.Flask(__name__)
        app.add_url_rule(
            "/info", view_func=ModuleInfo.as_view("modules_list", self.lnxlink)
        )
        app.add_url_rule(
            "/info/<module>", view_func=ModuleInfo.as_view("module_info", self.lnxlink)
        )
        app.add_url_rule(
            "/control", view_func=ModuleControl.as_view("control_list", self.lnxlink)
        )
        app.add_url_rule(
            "/control/<module>",
            view_func=ModuleControl.as_view("control", self.lnxlink),
        )
        threading.Thread(target=self._serve, args=[app], daemon=True).start()

    def _serve(self, app):
        waitress = import_install_package("waitress", ">=3.0.0", "waitress")
        port = self.lnxlink.config["settings"].get("restful", {}).get("port", 8112)
        waitress.serve(app, host="0.0.0.0", port=port)
