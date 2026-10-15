"""Idempotent demo bootstrap. All content is explicitly fictional."""
from pathlib import Path
import secrets
from datetime import date, datetime, timedelta
from sqlalchemy import select
from alembic import command
from alembic.config import Config
from . import models as m
from .db import Base, engine, SessionLocal
from .config import settings
from .security import hash_password
from .catalog import MODULES


def seed():
    if not settings.demo_mode or settings.app_env == 'production':
        raise RuntimeError('El seed solo está habilitado en entornos de demostración.')
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    config.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'migrations'))
    command.upgrade(config, 'head')
    with SessionLocal() as db:
        if db.scalar(select(m.User.id)):
            print('La base ya contiene usuarios. No se modificó ningún registro.')
            return
        password = settings.demo_password or secrets.token_urlsafe(18)
        if len(password) < 12:
            raise RuntimeError('DEMO_PASSWORD debe tener al menos 12 caracteres.')
        demo_accounts = [
            ('Administración demo', 'admin@example.invalid', 'administrador'),
            ('Lucía · demo', 'jefatura@example.invalid', 'jefatura'),
            ('Mateo · demo', 'coordinador@example.invalid', 'coordinador'),
            ('Elena · demo', 'integrante@example.invalid', 'integrante'),
            ('Auditoría demo', 'auditor@example.invalid', 'consulta_auditoria'),
        ]
        users = []
        for name, email, _ in demo_accounts:
            user = m.User(name=name, email=email, password_hash=hash_password(password))
            db.add(user)
            users.append(user)
        db.flush()
        admin, chief, coordinator, member, auditor = users
        for user in users:
            user.modified_by = admin.id
        all_permissions = {}
        for module in MODULES:
            for action in ('read', 'write', 'validate'):
                permission = m.Permission(name=f'{module}.{action}', modified_by=admin.id)
                db.add(permission)
                db.flush()
                all_permissions[permission.name] = permission
        for name in ('tasks.supervise', 'tasks.team_read'):
            permission = db.scalar(select(m.Permission).where(m.Permission.name == name))
            if not permission:
                permission = m.Permission(name=name, modified_by=admin.id)
                db.add(permission)
                db.flush()
            all_permissions[name] = permission
        for (_, _, role_name), user in zip(demo_accounts, users):
            role = m.Role(name=role_name, modified_by=admin.id)
            db.add(role)
            db.flush()
            db.add(m.UserRole(user_id=user.id, role_id=role.id, modified_by=admin.id))
            for name, permission in all_permissions.items():
                module, action = name.split('.')
                allowed = role_name in ('administrador', 'jefatura')
                if role_name == 'coordinador':
                    allowed = module != 'admin' and (module != 'audit' or action == 'read')
                if role_name == 'integrante':
                    allowed = module not in {'admin', 'audit'} and action in {'read', 'write'} and (module != 'reports' or action == 'read')
                if role_name == 'consulta_auditoria':
                    allowed = module != 'admin' and action == 'read'
                if name == 'tasks.supervise':
                    allowed = role_name in ('administrador', 'jefatura')
                if name == 'tasks.team_read':
                    allowed = role_name == 'consulta_auditoria'
                if allowed:
                    db.add(m.RolePermission(role_id=role.id, permission_id=permission.id, modified_by=admin.id))
        def add(cls, **kwargs):
            item = cls(**kwargs, modified_by=admin.id)
            db.add(item)
            db.flush()
            return item
        today = date.today()
        axes = [add(m.Axis, name=name, color=color) for name, color in [
            ('Gestión de la calidad · demo', '#13847b'), ('Acreditación · demo', '#6a65bc'), ('Gestión institucional · demo', '#da9546')]]
        processes = [add(m.Process, name=name, axis_id=axis.id) for name, axis in zip(['Mejora continua · demo', 'Autoevaluación · demo', 'Gestión documental · demo'], axes)]
        titles = ['Plan de mejora institucional · demo', 'Ruta de autoevaluación · demo', 'Organización del archivo digital · demo']
        projects = [add(m.Project, title=title, description='Proyecto ficticio para explorar el sistema.', axis_id=axis.id, process_id=process.id,
                        responsible_id=owner.id, start_date=today - timedelta(days=35), due_date=today + timedelta(days=60))
                    for title, axis, process, owner in zip(titles, axes, processes, [chief, coordinator, member])]
        tasks = []
        for i, (title, progress, days, status) in enumerate([
            ('Consolidar el diagnóstico de procesos · demo', 75, 3, 'en_progreso'),
            ('Revisar la matriz de compromisos · demo', 100, 2, 'en_revision'),
            ('Solicitar medios de verificación · demo', 30, -4, 'en_progreso'),
            ('Preparar informe de seguimiento · demo', 0, 6, 'pendiente'),
            ('Actualizar inventario de documentos · demo', 60, 12, 'en_progreso'),
            ('Coordinar mesa de trabajo · demo', 0, 5, 'pendiente'),
            ('Revisar avances semanales · demo', 40, -1, 'en_progreso'),
            ('Ordenar evidencias del periodo · demo', 100, 15, 'en_revision'),
        ]):
            owner = [member, coordinator, chief][i % 3]
            task = add(m.Task, title=title, description='Actividad ficticia; no representa compromisos institucionales.', project_id=projects[i % 3].id,
                       responsible_id=owner.id, created_by=chief.id, start_date=today - timedelta(days=14), due_date=today + timedelta(days=days),
                       progress=progress, status=status, priority='alta' if days < 0 else 'media')
            tasks.append(task)
            add(m.TaskAssignment, task_id=task.id, user_id=owner.id, assigned_by=chief.id)
            add(m.TaskUpdate, task_id=task.id, author_id=owner.id, progress=progress, comment='Avance de demostración.', kind='avance')
        for p in projects:
            add(m.Milestone, title='Revisión de resultados · demo', project_id=p.id, due_date=today + timedelta(days=30))
        types = {name: add(m.DocumentType, name=name) for name in ['Carta', 'Carta múltiple', 'Informe', 'Informe técnico', 'Memorando', 'Oficio', 'Documento recibido', 'Directiva', 'Plan', 'Reglamento', 'Manual', 'Otro']}
        docs = []
        for i, (title, section, typ) in enumerate([('Solicitud de revisión · demo', 'recibidos', 'Documento recibido'), ('Informe de avance · demo', 'emitidos', 'Informe'), ('Plan de trabajo · demo', 'normativos', 'Plan'), ('Carta de coordinación · demo', 'emitidos', 'Carta')]):
            docs.append(add(m.Document, title=title, number=f'DEMO-{i+1:03}', year=today.year, document_type_id=types[typ].id, section=section,
                            date=today, sender='Área ficticia A', recipient='Área ficticia B', responsible_id=member.id,
                            project_id=projects[0].id, due_date=today + timedelta(days=10)))
        add(m.TaskDocument, task_id=tasks[0].id, document_id=docs[0].id)
        case = add(m.Case, title='Revisión del informe · demo', number='EXP-DEMO-001', document_id=docs[1].id,
                   responsible_id=member.id, current_department='Área externa ficticia', due_date=today + timedelta(days=10))
        add(m.CaseEvent, case_id=case.id, actor_id=member.id, status='elaboracion', department=case.current_department, note='Apertura ficticia del expediente.')
        meeting = add(m.Meeting, title='Mesa de seguimiento · demo', date=datetime.combine(today + timedelta(days=2), datetime.min.time()).replace(hour=10),
                      agenda='1. Avances del periodo\n2. Evidencias pendientes\n3. Nuevos compromisos', location='Sala de demostración', responsible_id=coordinator.id, project_id=projects[0].id)
        for user in [chief, coordinator, member]:
            add(m.Attendee, meeting_id=meeting.id, user_id=user.id)
        add(m.Agreement, title='Consolidar compromisos de la mesa · demo', meeting_id=meeting.id, project_id=projects[0].id, responsible_id=member.id, due_date=today + timedelta(days=7))
        add(m.Evidence, title='Matriz de seguimiento · demo', category='Matriz', date=today, author_id=member.id, requested_department='Área ficticia', due_date=today + timedelta(days=5), request_status='solicitada')
        order = add(m.ServiceOrder, title='Apoyo de seguimiento · demo', number='OS-DEMO-001', provider='Prestador ficticio', responsible_id=coordinator.id,
                    project_id=projects[0].id, start_date=today - timedelta(days=10), due_date=today + timedelta(days=30))
        add(m.Deliverable, title='Primer informe de actividades · demo', service_order_id=order.id, responsible_id=coordinator.id, due_date=today + timedelta(days=6))
        model = add(m.QualityModel, title='Modelo ficticio de demostración', version='DEMO, sin vigencia normativa')
        criterion = add(m.Criterion, title='Criterio ficticio de seguimiento', code='DEMO-01', quality_model_id=model.id)
        period = add(m.Period, name=f'{today.year} · demo', start_date=date(today.year, 1, 1), end_date=date(today.year, 12, 31))
        indicator = add(m.Indicator, title='Compromisos con seguimiento · demo', criterion_id=criterion.id, responsible_id=chief.id, project_id=projects[0].id)
        add(m.IndicatorResult, indicator_id=indicator.id, period_id=period.id, target=90, result=65)
        add(m.ImprovementPlan, title='Completar medios de verificación · demo', indicator_id=indicator.id, responsible_id=chief.id, due_date=today + timedelta(days=20))
        db.add(m.Audit(actor_id=admin.id, entity='demo', record_id=admin.id, action='seed', after={'notice': 'Todos los registros son ficticios.'}))
        db.commit()
        destination = Path(__file__).resolve().parents[2] / '.local/demo-access.txt'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text('CUENTAS FICTICIAS, SOLO PARA PRUEBAS LOCALES\n' + '\n'.join(f'{email} ({role})' for _, email, role in demo_accounts) + '\nContraseña de demostración: ' + password + '\n', encoding='utf-8')
        print('Demostración creada. Credenciales locales en .local/demo-access.txt (ignorado por Git).')


if __name__ == '__main__':
    seed()
