# -*- coding: utf-8 -*-

from odoo import models, fields

class Subject(models.Model):
  """
  Añade a la asignatura las aulas virtuales de Moodle
  """

  _inherit = 'maya_core.subject'

  # Aulas virtuales asignadas a este módulo
  classrooms_ids = fields.One2many('maya_moodle.subject_classroom_rel', 'subject_id', string = 'Aulas virtuales')

  def get_classroom_by_study_id(self, study):
    """
    Devuelve el aula virtual asociada a este módulo para un ciclo determinado
    """
    self.ensure_one()

    return self.classrooms_ids.filtered(lambda t: t.study_id.id == study.id)['classroom_id']
