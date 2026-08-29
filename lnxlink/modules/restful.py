"""Expose sensors as a Restful API"""
import base64
import json
import logging
import threading
import traceback
from urllib.parse import urlparse

from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "RESTful"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings(
            "restful",
            {
                "host": "0.0.0.0",
                "port": 8112,
                "username": "",
                "password": "",
            },
        )
        self._requirements()

    def _requirements(self):
        flask_view = import_install_package("flask", ">=3.0.3", "flask.views")
        flask = import_install_package("flask", ">=3.0.3", "flask")

        def json_response(payload):
            """Return JSON with an explicit application/json content type."""
            if isinstance(payload, bytes):
                payload = payload.decode("UTF-8", errors="replace")
            return flask.Response(
                json.dumps(payload),
                mimetype="application/json",
            )

        class ModuleInfo(flask_view.views.MethodView):
            """Get information from Addon modules"""

            def __init__(self, lnxlink):
                """Init the application"""
                self.lnxlink = lnxlink

            def get(self, module=None):
                """Fetch data from modules"""
                info = self.lnxlink.saved_publish
                if module is None:
                    return json_response(list(info.keys()))
                return json_response(info.get(module))

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
                return json_response(modules)

            def post(self, module=None):
                """Control an Addon module"""
                if module is None:
                    modules = []
                    for addonmodule, addon in self.lnxlink.addons.items():
                        if hasattr(addon, "start_control"):
                            modules.append(addonmodule)
                    return json_response(modules)

                topic = flask.request.form.get("topic", "")
                topic = f"{module}/{topic}"
                topic = topic.split("/")
                message = flask.request.form.get("message")
                addon = self.lnxlink.addons.get(module)
                if addon is not None:
                    if hasattr(addon, "start_control"):
                        try:
                            result = addon.start_control(topic, message)
                            return json_response(result)
                        except Exception as err:
                            logger.error(
                                "Couldn't run command for module %s: %s, %s",
                                addon,
                                err,
                                traceback.format_exc(),
                            )
                            return json_response(f"Error: {err}")
                    return json_response("No control support available")
                return json_response("Module not found")

        app = flask.Flask(__name__)
        app.before_request(lambda: self._authenticate(flask, json_response))
        app.add_url_rule(
            "/",
            endpoint="swagger_ui",
            view_func=lambda: flask.Response(
                self._swagger_html(), mimetype="text/html"
            ),
        )
        app.add_url_rule(
            "/openapi.json",
            endpoint="openapi_spec",
            view_func=lambda: json_response(self._get_spec()),
        )
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

    def _check_csrf(self, flask, json_response):
        """Block cross-site browser requests on state-changing methods"""
        if flask.request.method != "POST":
            return None

        if flask.request.headers.get("Sec-Fetch-Site") == "cross-site":
            response = json_response("Forbidden: Cross-site request blocked")
            response.status_code = 403
            return response

        source = flask.request.headers.get("Origin") or flask.request.headers.get(
            "Referer"
        )
        if source:
            source_host = urlparse(source).netloc
            if source_host and source_host != flask.request.host:
                response = json_response("Forbidden: Invalid origin")
                response.status_code = 403
                return response
        return None

    def _authenticate(self, flask, json_response):
        """Authenticate request using HTTP Basic Auth if configured and block CSRF"""
        if flask.request.path in ["/", "/openapi.json"]:
            return None

        csrf_response = self._check_csrf(flask, json_response)
        if csrf_response is not None:
            return csrf_response

        settings = self.lnxlink.config.get("settings", {}).get("restful", {})
        expected_user = str(settings.get("username") or settings.get("user") or "")
        expected_pass = str(settings.get("password") or settings.get("pass") or "")

        # If username and password are not configured, authentication is disabled
        if not expected_user and not expected_pass:
            return None

        auth = flask.request.authorization
        if auth and (auth.type is None or auth.type == "basic"):
            req_user = str(auth.username or "")
            req_pass = str(auth.password or "")
            if req_user == expected_user and req_pass == expected_pass:
                return None

        # Fallback check for raw Authorization header
        auth_header = flask.request.headers.get("Authorization", "")
        if auth_header.startswith("Basic "):
            try:
                encoded = auth_header.split(" ", 1)[1].strip()
                decoded = base64.b64decode(encoded).decode("UTF-8", errors="replace")
                if ":" in decoded:
                    req_user, req_pass = decoded.split(":", 1)
                    if req_user == expected_user and req_pass == expected_pass:
                        return None
            except Exception:
                pass

        response = json_response("Unauthorized")
        response.status_code = 401
        response.headers["WWW-Authenticate"] = 'Basic realm="LNXlink RESTful"'
        return response

    def _swagger_html(self):
        """Return Swagger UI HTML page"""
        spec = self._get_spec()
        return f"""<!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>LNXlink RESTful API</title>
              <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
              <style>
                body {{ margin: 0; background: #fafafa; }}
                .topbar {{ display: none; }}
              </style>
            </head>
            <body>
              <div id="swagger-ui"></div>
              <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin="anonymous"></script>
              <script>
                window.onload = () => {{
                  window.ui = SwaggerUIBundle({{
                    spec: {json.dumps(spec)},
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                      SwaggerUIBundle.presets.apis,
                    ],
                  }});
                }};
              </script>
            </body>
            </html>"""

    def _get_spec(self):
        """Generate OpenAPI 3.0 specification for LNXlink RESTful API"""
        control_modules = [
            name
            for name, addon in self.lnxlink.addons.items()
            if hasattr(addon, "start_control")
        ]
        info_modules = list(self.lnxlink.saved_publish.keys())

        info_desc = (
            f"Name of the module (currently active: {', '.join(info_modules)})"
            if info_modules
            else "Name of the module (e.g. cpu, memory, battery)"
        )
        control_desc = (
            f"Name of the module to control (available: {', '.join(control_modules)})"
            if control_modules
            else "Name of the module to control (e.g. shutdown, restart, media)"
        )

        return {
            "openapi": "3.0.3",
            "info": {
                "title": "LNXlink RESTful API",
                "version": "1.0.0",
                "description": (
                    "RESTful API to inspect sensor data and execute controls "
                    "on LNXlink modules."
                ),
            },
            "paths": {
                "/info": {
                    "get": {
                        "summary": "List all available modules with sensor data",
                        "description": (
                            "Returns a list of module names that have published data."
                        ),
                        "responses": {
                            "200": {
                                "description": "List of available module names",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "example": info_modules,
                                        }
                                    }
                                },
                            },
                            "401": {"description": "Unauthorized"},
                        },
                    }
                },
                "/info/{module}": {
                    "get": {
                        "summary": "Get sensor data for a specific module",
                        "description": (
                            "Fetch the latest published data for the specified module."
                        ),
                        "parameters": [
                            {
                                "name": "module",
                                "in": "path",
                                "required": True,
                                "description": info_desc,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Module sensor data",
                                "content": {"application/json": {}},
                            },
                            "401": {"description": "Unauthorized"},
                        },
                    }
                },
                "/control": {
                    "get": {
                        "summary": "List all control-capable modules",
                        "description": (
                            "Returns a list of module names that support remote control."
                        ),
                        "responses": {
                            "200": {
                                "description": "List of control modules",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "example": control_modules,
                                        }
                                    }
                                },
                            },
                            "401": {"description": "Unauthorized"},
                        },
                    },
                    "post": {
                        "summary": "List all control-capable modules (POST fallback)",
                        "description": (
                            "Returns the list of modules that support control "
                            "when no module is specified."
                        ),
                        "responses": {
                            "200": {
                                "description": "List of control modules",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        }
                                    }
                                },
                            },
                            "401": {"description": "Unauthorized"},
                        },
                    },
                },
                "/control/{module}": {
                    "post": {
                        "summary": "Send a control command to an addon module",
                        "description": (
                            "Execute a control command on the specified addon module."
                        ),
                        "parameters": [
                            {
                                "name": "module",
                                "in": "path",
                                "required": True,
                                "description": control_desc,
                                "schema": {"type": "string"},
                            }
                        ],
                        "requestBody": {
                            "required": False,
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "topic": {
                                                "type": "string",
                                                "description": (
                                                    "Subtopic for the control action "
                                                    "(optional)"
                                                ),
                                            },
                                            "message": {
                                                "type": "string",
                                                "description": (
                                                    "Command message or payload"
                                                ),
                                            },
                                        },
                                    }
                                },
                            },
                            "responses": {
                                "200": {
                                    "description": "Result of the control execution",
                                    "content": {"application/json": {}},
                                },
                                "401": {"description": "Unauthorized"},
                            },
                        },
                    },
                },
            },
            "components": {
                "securitySchemes": {
                    "basicAuth": {
                        "type": "http",
                        "scheme": "basic",
                        "description": (
                            "HTTP Basic Authentication using username and password "
                            "configured in restful settings."
                        ),
                    }
                }
            },
            "security": [{"basicAuth": []}],
        }

    def _serve(self, app):
        waitress = import_install_package("waitress", ">=3.0.0", "waitress")
        settings = self.lnxlink.config.get("settings", {}).get("restful", {})
        host = settings.get("host") or "0.0.0.0"
        port = settings.get("port", 8112)
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 8112
        waitress.serve(app, host=host, port=port)
