import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models as m
from app.db import Base
from app.document_registry import next_number


class DocumentNumberConcurrencyTest(unittest.TestCase):
    def test_simultaneous_saves_allocate_distinct_numbers_and_rollback_releases_reservation(self):
        folder = Path(__file__).resolve().parents[2] / '.local'
        folder.mkdir(exist_ok=True)
        database = folder / f'test-document-numbers-{m.uid()}.db'
        engine = create_engine('sqlite:///' + database.as_posix(),
                               connect_args={'check_same_thread': False, 'timeout': 20})
        try:
            Base.metadata.create_all(engine)
            factory = sessionmaker(bind=engine)
            with factory.begin() as db:
                typ = m.DocumentType(name='Carta')
                db.add(typ)
                db.flush()
                type_id = typ.id
            with factory() as db:
                self.assertEqual(next_number(db, type_id, 2026, reserve=True)['sequence'], 1)
                db.rollback()
            def assign(_):
                with factory.begin() as db:
                    return next_number(db, type_id, 2026, reserve=True)['sequence']
            with ThreadPoolExecutor(max_workers=6) as pool:
                assigned = list(pool.map(assign, range(20)))
            self.assertEqual(sorted(assigned), list(range(1, 21)))
            with factory() as db:
                self.assertEqual(next_number(db, type_id, 2026)['sequence'], 21)
                self.assertEqual(next_number(db, type_id, 2027)['sequence'], 1)
        finally:
            engine.dispose()
            database.unlink(missing_ok=True)
