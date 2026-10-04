{
    'name': 'L10n VE Compliance Manager',
    'version': '19.0.1.0.0',
    'author': 'Eurick Ospino',
    'website': 'https://github.com/MrErov/contafis-odoo-19.0v',
    'category': 'Accounting/Localizations',
    'summary': 'Gestión de cumplimiento fiscal, parafiscal y documental para Venezuela',
    'description': """
Módulo Odoo 19.0 para contadores y firmas contables que gestionan múltiples
clientes en Venezuela.

Incluye:
- Calendario SENIAT 2026 con cálculo de vencimientos por RIF.
- Seguimiento de obligaciones fiscales, parafiscales y municipales.
- Cartelera fiscal documental con alertas de renovación.
- Alertas por email y WhatsApp (wa.me).
- Dashboard de cumplimiento por cliente.
- Retenciones de IVA/ISLR/IGTF vinculadas a facturas de proveedor.
    """,
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'mail', 'l10n_ve'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/mail_templates.xml',
        'data/cron.xml',
        'data/ir_sequence.xml',
        'data/seniat_calendar_2026.xml',
        'data/institution_data.xml',
        'data/document_type_cartelera.xml',
        'report/compliance_report.xml',
        'views/institution_views.xml',
        'views/obligation_type_views.xml',
        'views/document_views.xml',
        'views/alert_views.xml',
        'views/compliance_client_views.xml',
        'views/obligation_views.xml',
        'views/account_move_views.xml',
        'views/menu.xml',
        'views/import_views.xml',
        'views/cartelera_status_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}