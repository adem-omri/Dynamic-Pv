{
    'name': 'PV Dynamic',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Dynamic PV management module following strict architectural rules.',
    'description': "",
    'author': 'Adem Omri',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/pv_modele_demo.xml',
        'views/pv_modele_views.xml',
        'views/pv_pv_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
