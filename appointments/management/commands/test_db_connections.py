from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import mysql.connector

class Command(BaseCommand):
    help = 'Test database connections and fetch sample data'

    def handle(self, *args, **options):
        for db_name in connections:
            try:
                self.stdout.write(self.style.NOTICE(f'\nTesting connection for {db_name}...'))
                cursor = connections[db_name].cursor()
                
                # Skip detailed testing for SQLite
                if db_name == 'default':
                    self.stdout.write(self.style.SUCCESS(f'Successfully connected to SQLite database'))
                    continue

                # Test connection
                self.stdout.write(self.style.SUCCESS(f'Successfully connected to {db_name}'))

                # Get list of tables
                if db_name == 'hospital1':  # PostgreSQL
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                elif db_name == 'hospital2':  # MySQL
                    cursor.execute("SHOW TABLES")
                
                tables = cursor.fetchall()
                
                if not tables:
                    self.stdout.write(self.style.WARNING(f'No tables found in {db_name}'))
                    continue

                # Display tables and sample data
                self.stdout.write(self.style.NOTICE(f'\nTables in {db_name}:'))
                for table in tables:
                    table_name = table[0]
                    self.stdout.write(f'\n→ Table: {table_name}')

                    # Get column information
                    if db_name == 'hospital1':  # PostgreSQL
                        cursor.execute(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table_name}'
                        """)
                    elif db_name == 'hospital2':  # MySQL
                        cursor.execute(f"DESCRIBE {table_name}")
                    
                    columns = cursor.fetchall()
                    self.stdout.write("  Columns:")
                    for col in columns:
                        self.stdout.write(f"    - {col[0]}: {col[1]}")

                    # Get sample data
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        rows = cursor.fetchall()
                        if rows:
                            self.stdout.write("  Sample Data:")
                            for row in rows:
                                self.stdout.write(f"    {row}")
                        else:
                            self.stdout.write("  No data in table")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Error fetching data: {str(e)}"))

            except OperationalError as e:
                self.stdout.write(self.style.ERROR(f'Failed to connect to {db_name}: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error while testing {db_name}: {str(e)}'))
            finally:
                if 'cursor' in locals():
                    cursor.close()

    def format_row(self, row):
        """Helper function to format row data nicely"""
        return ' | '.join(str(value) for value in row)