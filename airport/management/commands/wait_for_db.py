import time

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Waiting for the database...")
        db_conn = None

        while not db_conn:
            try:
                connection.ensure_connection()
                db_conn = True
            except OperationalError:
                self.stdout.write(
                    "The database is unavailable: "
                    "please wait one more second..."
                )
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("The database is available!"))
