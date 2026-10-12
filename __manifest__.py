# -*- coding: utf-8 -*-
{
    'name': "Maya | Moodle",
    'version': '19.0.1.0',

    'summary': """
        Extensión de Maya | Core para la conexión con Moodle (Aules) a través de maya-moodlink""",

    'website': "https://portal.edu.gva.es/ceedcv/",
    'author': 'Alfredo Oltra',
    'maintainer': 'Alfredo Oltra <alfredo.ptcf@gmail.com>',
    'company': '',
    'category': 'Productivity',

    'license': 'AGPL-3',
    # precio del módulo
    'price': 0,

    # any module necessary for this one to work correctly
    'depends': ['base', 'maya_core'],

    # always loaded
    'data': [
        'views/res_config_settings.xml',   
        'views/res_user.xml',   
    ],
    'installable': True,
    'application': False,
}