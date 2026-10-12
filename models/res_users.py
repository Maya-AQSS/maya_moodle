from odoo import fields, models


class ResUsers(models.Model):
  """
  Datos de Moodle de cada usuario de Odoo.

  El token se guarda CIFRADO con una clave que Odoo NO tiene (solo el gateway). Lo escribe
  Odoo con su ORM (el gateway no tiene permiso de escritura en la BD) y lo lee el gateway
  directamente de la tabla res_users, solo las columnas moodle_token_enc, moodle_username,
  active e id (ver sql/grants.sql).
  """

  _inherit = "res.users"

  # Explícito, no calculado. Profesores: su DNI/NIE (se rellena solo en el primer acceso a
  # partir del login). Administradores: se configura a mano.
  moodle_username = fields.Char(
    string="Usuario de Moodle",
    copy=False,
    help="Usuario con el que esta persona entra en Moodle. Si se deja vacío, se usará "
    "el login de Odoo (DNI/NIE) la primera vez que se identifique.",
  )
  
  moodle_token_enc = fields.Text(
    string="Token de Moodle (cifrado)",
    copy=False,
    readonly=True,
    groups="base.group_system",
    prefetch=False,
    help="Cifrado por el gateway. Odoo no puede descifrarlo.",
  )
  moodle_token_date = fields.Datetime(
    string="Token de Moodle obtenido el", copy=False, readonly=True, groups="base.group_system"
  )
  moodle_has_token = fields.Boolean(
    string="Tiene token de Moodle", compute="_compute_moodle_has_token", compute_sudo=True
  )

  def _compute_moodle_has_token(self):
    for user in self:
        user.moodle_has_token = bool(user.moodle_token_enc)

  def write(self, vals):
    # Si cambia el usuario de Moodle, el token guardado ya no corresponde a esa persona.
    reset = self.browse()
    if "moodle_username" in vals and "moodle_token_enc" not in vals:
        new = vals["moodle_username"] or ""
        reset = self.filtered(lambda u: (u.moodle_username or "") != new)

    res = super().write(vals)

    # Al archivar a un usuario se borra su token: no debe seguir pudiendo operar en Moodle.
    if vals.get("active") is False:
        reset |= self
    if reset:
        reset.sudo().write({"moodle_token_enc": False, "moodle_token_date": False})
    return res
