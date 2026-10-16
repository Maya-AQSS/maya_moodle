from markupsafe import escape

from odoo import _, http
from odoo.http import request

from ..models.moodlink import MoodleGatewayError

PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Moodle</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:26rem;margin:4rem auto;padding:0 1rem}
 label{display:block;margin-top:1rem}
 input{width:100%;padding:.5rem;box-sizing:border-box}
 button{margin-top:1.5rem;padding:.6rem 1.2rem}
 .err{color:#b00020}.ok{color:#1b5e20}
</style></head>
<body><h2>Identifícate en Moodle</h2>__BODY__</body></html>"""


class MoodleTokenController(http.Controller):
  """
  Formulario donde el usuario escribe su contraseña de Moodle.

  Se hace con un controlador HTTP y NO con un wizard (TransientModel) a propósito: los
  campos de un wizard se guardan en la base de datos de Odoo, y la contraseña acabaría
  en la BD, en el WAL y en las copias de seguridad. Aquí la contraseña solo existe en
  memoria durante la petición y viaja directamente al gateway.

  El usuario de Moodle NO se pide: es el moodle_username del usuario de Odoo (o su login,
  es decir, su DNI/NIE, la primera vez). Así nadie puede identificarse como otra persona.
  Sirve la página por HTTPS (en producción, Odoo detrás de un proxy con TLS).
  """

# '/api/v1/student/notify-itaca-datafile-ready',
  @http.route("/maya/moodle/token", type="http", auth="user", methods=["GET", "POST"], csrf=True)
  def moodle_token(self, password=None, **kw):
    user = request.env.user
    gateway = request.env["maya_moodle.moodlink"]

    if request.httprequest.method == "POST":
        try:
            gateway.request_token(user, password or "")
        except MoodleGatewayError as e:
            if e.code == "invalid_credentials":
                message = _("Usuario o contraseña de Moodle incorrectos.")
            else:
                message = str(e)
            return self._respond(self._form(user, error=message))
        done = _("Listo. Ya puedes cerrar esta ventana y repetir la operación.")
        return self._respond('<p class="ok">%s</p>' % escape(done))

    return self._respond(self._form(user))

  # ---------------------------------------------------------------

  def _form(self, user, error=None):
    parts = []
    if error:
        parts.append('<p class="err">%s</p>' % escape(error))
    parts.append(
        "<p>%s <strong>%s</strong></p>"
        % (escape(_("Usuario de Moodle:")), escape(user.moodle_username or user.login))
    )
    parts.append('<form method="post" action="/maya/moodle/token" autocomplete="off">')
    parts.append('<input type="hidden" name="csrf_token" value="%s"/>' % escape(request.csrf_token()))
    parts.append(
        '<label>%s<input type="password" name="password" required autocomplete="current-password"/></label>'
        % escape(_("Contraseña de Moodle"))
    )
    parts.append('<button type="submit">%s</button></form>' % escape(_("Continuar")))
    return "".join(parts)

  def _respond(self, body):
    return request.make_response(
        PAGE.replace("__BODY__", body),
        headers=[
            ("Content-Type", "text/html; charset=utf-8"),
            ("Cache-Control", "no-store"),
        ],
    )
