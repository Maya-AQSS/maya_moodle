# -*- coding: utf-8 -*-

from odoo import models
import toolz
import logging

_logger = logging.getLogger(__name__)

class SchoolYear(models.Model):
  """
  Añade al curso escolar las tareas cron que dependen de las aulas virtuales de Moodle
  """

  _inherit = 'maya_core.school_year'

  def _get_cron_tasks(self):
    """
    Añade a las tareas de maya_core las tareas cron de las aulas de tutoría:
    - matriculación
    """
    cron_ids = super()._get_cron_tasks()

    studies = self.env['maya_core.study'].search([])

    # creación de cron jobs para los ciclos de manera independiente
    _logger.info('Creando cron por ciclo de manera independiente => aulas de tutoria')
    for study in studies:
      # módulos de tutoria
      _logger.info(f'Ciclo -> {study.abbr}')
      tut_subjects = [ subject for subject in study.subjects_ids if subject['code'][:3] == 'TUT']

      _logger.info(f'Tutorias: {tut_subjects}')
      if not tut_subjects:
        _logger.error('No hay módulos de tutoria asignados en {}'.format(study.abbr))
        continue

      # únicamente módulos de tutoria que tengan aulas distintas
      distinct_subject_tut = [subject for subject in list(toolz.unique(tut_subjects, key = lambda x: x.get_classroom_by_study_id(study)))]
    
      # por cada aula de tutoria que haya en ese ciclo
      for subject in distinct_subject_tut:   
        classroom_id = subject.get_classroom_by_study_id(study)

        if classroom_id.moodle_id == 0:
          _logger.error(f'No hay definida en Maya un aula virtual de tutoria para {study.name}')
          continue

        ## MATRICULA 
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'MTAL')])
        task_name = 'Matricula alumnos de {} en Maya {}'.format(study.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')

        job_data = { 'classroom_id': classroom_id.moodle_id,
                     'course_id': study.id,
                     'subject_id': subject.id}

        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        """ ## CONVALIDACIONES ESTE BLOQUE HAYQUE LLEVARSELO  A MAYA_VALID
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'DVAL')])
        task_name = 'Descarga datos convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
        
        job_data = { 'validation_classroom_id': classroom_id.moodle_id,
                     'course_id': course.id,
                     'subject_id': subject.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('validation') }

        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## RECLAMACIONES CONVALIDACIONES
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'DVAC')])
        task_name = 'Descarga datos reclamación convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')

        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id,
                     'subject_id': subject.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('validation_claim')}

        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## NOTIFICACIONES ALUMNADO
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'NOTV')])
        task_name = 'Notifica estado convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
      
        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('validation'), 
                     'validation_claim_task_id': classroom_id.get_task_id_by_key('validation_claim'), 
                     }
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## NOTIFICACIONES RECLAMACION ALUMNADO
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'NTCV')])
        task_name = 'Notifica estado reclamación convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')

        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id, 
                     'validation_claim_task_id': classroom_id.get_task_id_by_key('validation_claim')}
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## CONVALIDACIONES COMPETENCIAS
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'DVUC')])
        task_name = 'Descarga datos convalidaciones por competencias {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
        
        job_data = { 'validation_classroom_id': classroom_id.moodle_id,
                     'course_id': course.id,
                     'subject_id': subject.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('competence'), 
                     'val_type': 1 }
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

         ## NOTIFICACIONES ALUMNADO
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'NVUC')])
        task_name = 'Notifica estado convalidaciones por competencias {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
        
        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('competence'), 
                     'validation_claim_task_id': classroom_id.get_task_id_by_key('competence_claim'), 
                     'val_type': 1 }
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task) """

    return cron_ids
