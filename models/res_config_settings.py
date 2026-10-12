from odoo import fields, models


class ResConfigSettings(models.TransientModel):
  _inherit = "res.config.settings"

  maya_moodle_gateway_url = fields.Char(
      string="URL del gateway de Moodle",
      config_parameter="maya_moodle.gateway_url",
      help="Por ejemplo: http://maya-noodlink:8080 (sin barra final).",
  )
