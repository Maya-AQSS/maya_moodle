from odoo import fields, models


class ResConfigSettings(models.TransientModel):
  _inherit = "res.config.settings"

  maya_moodle_gateway_url = fields.Char(
      string="URL del gateway de Moodle",
      config_parameter="maya_moodle.gateway_url",
      help="Por ejemplo: http://maya-noodlink:8080 (sin barra final).",
  )

  maya_moodle_service_user_id = fields.Many2one(
      "res.users",
      string="Usuario de servicio de Moodle",
      config_parameter="maya_moodle.service_user_id",
      help="Usuario técnico (Maya) con el que se opera en Moodle desde procesos automáticos. "
      "Tiene que estar dado de alta como cuenta de servicio en el gateway.",
  )
