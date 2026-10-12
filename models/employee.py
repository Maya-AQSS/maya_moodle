from odoo import fields, models


class Employee(models.Model):
    """Muestra en el empleado el usuario de Moodle"""

    _inherit = "maya_core.employee"

    moodle_username = fields.Char(string="Usuario de Moodle", related="user_id.moodle_username")
