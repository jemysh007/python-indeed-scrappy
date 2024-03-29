import argparse
import csv
import mysql.connector
from prettytable import PrettyTable
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

class IndeedJobDatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect_to_database()

    def connect_to_database(self):
        try:
            
            print(os.getenv("DB_HOST"))
            print(os.getenv("DB_USER"))
            print(os.getenv("DB_PASSWORD"))
            print(os.getenv("DB_NAME"))

            self.conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
            print("Connected to the database")
        except mysql.connector.Error as e:
            print(f"Error: {e}")

    def view_data(self, location, title):
        try:
            cursor = self.conn.cursor()
            if not title and location:
                # Only location provided
                cursor.execute("""
                    SELECT id, title, company, job_link, location, date_of_post, created_on
                    FROM indeed_jobs
                    WHERE location_search LIKE %s
                    ORDER BY date_of_post DESC
                """, (f"%{location}%",))

            elif title and not location:
                # Only title provided
                cursor.execute("""
                    SELECT id, title, company, job_link, location, date_of_post, created_on
                    FROM indeed_jobs
                    WHERE title_search LIKE %s
                    ORDER BY date_of_post DESC
                """, (f"%{title}%",))

            else:
                # Both title and location provided
                cursor.execute("""
                    SELECT id, title, company, job_link, location, date_of_post, created_on
                    FROM indeed_jobs
                    WHERE location_search LIKE %s AND title_search LIKE %s
                    ORDER BY date_of_post DESC
                """, (f"%{location}%", f"%{title}%"))

            results = cursor.fetchall()

            if not results:
                print("No matching data found.")
                return

            table = PrettyTable()
            table.field_names = ["ID", "Title", "Company", "Job Link", "Location", "Date of Post", "created_on"]

            for row in results:
                table.add_row(row)

            print(table)

        except mysql.connector.Error as e:
            print(f"Error: {e}")

    def delete_data(self, location, title):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM indeed_jobs
                WHERE location_search LIKE %s AND title_search LIKE %s
            """, (f"%{location}%", f"%{title}%"))

            self.conn.commit()
            print(f"Data deleted successfully.")

        except mysql.connector.Error as e:
            print(f"Error: {e}")

    def clear_table(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("TRUNCATE TABLE indeed_jobs")
            cursor.execute("ALTER TABLE indeed_jobs AUTO_INCREMENT = 1")  # Reset auto-increment primary key
            self.conn.commit()
            print("Table indeed_jobs cleared successfully.")

        except mysql.connector.Error as e:
            print(f"Error: {e}")

    def export_data(self, location, title):
        try:
            cursor = self.conn.cursor()
            if not title and location:
                cursor.execute("""
                    SELECT id, title, company, job_link, location, date_of_post, search_query, job_type
                    FROM indeed_jobs
                    WHERE location_search LIKE %s
                    ORDER BY date_of_post DESC
                """, (f"%{location}%",))

            elif title and not location:
                cursor.execute("""
                    SELECT id, title, company, job_link, location, date_of_post, search_query, job_type
                    FROM indeed_jobs
                    WHERE title_search LIKE %s
                    ORDER BY date_of_post DESC
                """, (f"%{title}%",))

            else:
                cursor.execute("""
                    SELECT id, title, company, job_link, location, date_of_post, search_query, job_type
                    FROM indeed_jobs
                    WHERE location_search LIKE %s AND title_search LIKE %s
                    ORDER BY date_of_post DESC
                """, (f"%{location}%", f"%{title}%"))

            results = cursor.fetchall()

            if not results:
                print("No matching data found for export.")
                return

            # Generate a unique timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            export_file_path = f"export_{location}_{title}_jobs_{timestamp}.csv"

            with open(export_file_path, 'w', newline='') as csvfile:
                fieldnames = ["id", "title", "company", "job_link", "location", "date_of_post", "search_query", "job_type"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for row in results:
                    # Extract only the relevant fields present in 'fieldnames'
                    writer.writerow(dict(zip(fieldnames, row)))

            print(f"Data exported to {export_file_path}")

        except mysql.connector.Error as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Indeed job database")
    parser.add_argument("command", choices=["view", "delete", "clear", "export"], help="Command to execute")
    parser.add_argument("--location", help="Location filter")
    parser.add_argument("--title", help="Title filter")

    args = parser.parse_args()

    manager = IndeedJobDatabaseManager()

    if args.command == "view":
        manager.view_data(args.location, args.title)
    elif args.command == "delete":
        manager.delete_data(args.location, args.title)
    elif args.command == "clear":
        manager.clear_table()
    elif args.command == "export":
        manager.export_data(args.location, args.title)
    else:
        print("Invalid command. Use 'view', 'delete', 'clear', or 'export'.")
