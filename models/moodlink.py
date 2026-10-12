import logging
import os

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

TIMEOUT = 30  # segundos
TOKEN_ERRORS = ("moodle_token_missing", "moodle_token_invalid")


class MoodleGatewayError(UserError):
  """Error devuelto por el gateway (o imposibilidad de contactar con él)."""

  def __init__(self, message, code=None):
      super().__init__(message)
      self.code = code


class MoodleTokenRequired(MoodleGatewayError):
  """401: el usuario no tiene token válido. Hay que pedirle su contraseña de Moodle."""


class MoodleForbidden(MoodleGatewayError):
  """403: Moodle (o el gateway) le niega el permiso. Volver a identificarse NO lo arregla."""


class MayaMoodleGateway(models.AbstractModel):
  """Cliente del gateway de Moodle.

  Configuración:
    * Ajustes > Maya Moodle > URL del gateway   (parámetro maya_moodle.gateway_url)
    * variable de entorno MAYA_GATEWAY_API_KEY  (la misma API_KEY del gateway)

  A Odoo solo le importa el usuario: nunca ve ni envía el token de Moodle. El gateway lo lee
  de res_users y lo descifra. Odoo solo reacciona a las respuestas:

      def action_ver_alumnos(self):
          gw = self.env["maya_moodle.moodlink"]
          try:
              alumnos = gw.get_students(self.moodle_course_id)["users"]
          except MoodleTokenRequired:
              return gw.token_prompt_action()      # 401: pedir la contraseña de Moodle
          except MoodleForbidden as e:
              raise UserError(_("Moodle no te permite ver esta aula: %s") % e)  # 403
          ...
  """

  _name = "maya_moodle.moodlink"
  _description = "Cliente del gateway de Moodle"

  # ------------------------------------------------------------ operaciones

  def get_students(self, course_id, include_teachers=False, user=None):
    params = {"include_teachers": "true"} if include_teachers else None
    return self._request("GET", "/v1/courses/%d/students" % int(course_id), user=user, params=params)

  def request_token(self, user, password):
    """
    Solicita un token a Moodle con la contraseña del usuario y lo guarda con el ORM.

    El gateway devuelve el token ya CIFRADO; Odoo lo guarda tal cual y no puede
    descifrarlo. La contraseña solo pasa por esta llamada: no se guarda, no se registra
    y no se escribe en ningún campo.
    """
    username = user.moodle_username or user.login  # profesores: su DNI/NIE
    data = self._request(
        "POST",
        "/v1/users/%d/token" % user.id,
        user=user,
        json={"username": username, "password": password},
    )
    vals = {"moodle_token_enc": data["token_enc"], "moodle_token_date": fields.Datetime.now()}
    if not user.moodle_username:
        vals["moodle_username"] = username
    user.sudo().write(vals)

  def token_prompt_action(self):
    """Acción de cliente que abre el formulario donde el usuario escribe su contraseña."""
    return {"type": "ir.actions.act_url", "url": "/maya/moodle/token", "target": "new"}

  # ------------------------------------------------------------ interno

  def _gateway_conf(self):
    base_url = (self.env["ir.config_parameter"].sudo().get_param("maya_moodle.gateway_url") or "").rstrip("/")
    api_key = os.environ.get("MAYA_GATEWAY_API_KEY", "")
    if not base_url or not api_key:
      raise UserError(
          _("El gateway de Moodle no está configurado (Ajustes > Maya Moodle y MAYA_GATEWAY_API_KEY).")
      )
    return base_url, api_key

  @staticmethod
  def _parse_error(resp):
    try:
      err = resp.json()["error"]
      return err.get("code"), err.get("message")
    except (ValueError, KeyError, AttributeError, TypeError):
      return None, None

  def _request(self, method, path, user=None, json=None, params=None):
    base_url, api_key = self._gateway_conf()
    user = user or self.env.user
    try:
      resp = requests.request(
          method,
          base_url + path,
          headers={"Authorization": "Bearer " + api_key, "X-Maya-User": str(user.id)},
          json=json,
          params=params,
          timeout=TIMEOUT,
      )
    except requests.RequestException:
      # No se registra la petición: el cuerpo puede contener la contraseña.
      _logger.warning("No se pudo contactar con el gateway de Moodle (%s %s)", method, path)
      raise MoodleGatewayError(_("No se pudo contactar con el servicio de Moodle."), code="gateway_unreachable")

    if resp.ok:
      return resp.json() if resp.content else None

    code, message = self._parse_error(resp)
    message = message or _("Error del servicio de Moodle (HTTP %s).") % resp.status_code
    if resp.status_code == 401 and code in TOKEN_ERRORS:
      raise MoodleTokenRequired(_("Debes identificarte en Moodle para continuar."), code=code)
    if resp.status_code == 403:
      raise MoodleForbidden(message, code=code)
    
    raise MoodleGatewayError(message, code=code)
