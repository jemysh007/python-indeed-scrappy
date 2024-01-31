import argparse
import csv
import mysql.connector
from mysql.connector import Error
from prettytable import PrettyTable
import datetime

class IndeedJobDatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect_to_database()

    def connect_to_database(self):
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="scrappy"
            )

            if self.conn.is_connected():
                print("Connected to the database")
        except Error as e:
            print(f"Error: {e}")

    def view_data(self, location, title):
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM indeed_jobs
                WHERE location LIKE %s AND title LIKE %s
            """, (f"%{location}%", f"%{title}%"))


            results = cursor.fetchall()

            if not results:
                print("No matching data found.")
                return

            table = PrettyTable()
            table.field_names = ["ID", "Title", "Company", "Job Link", "Location", "Date of Post"]

            for row in results:
                table.add_row([row["id"], row["title"], row["company"], row["job_link"], row["location"], row["date_of_post"]])

            print(table)

        except Error as e:
            print(f"Error: {e}")

    def delete_data(self, location, title):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM indeed_jobs
                WHERE location LIKE %s AND title LIKE %s
            """, (f"%{location}%", f"%{title}%"))

            self.conn.commit()
            print(f"Data deleted successfully.")

        except Error as e:
            print(f"Error: {e}")

    def clear_table(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("TRUNCATE TABLE indeed_jobs")
            self.conn.commit()
            print("Table indeed_jobs cleared successfully.")

        except Error as e:
            print(f"Error: {e}")

    def export_data(self, location, title):
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM indeed_jobs
                WHERE location LIKE %s AND title LIKE %s OR %s = ''
            """, (f"%{location}%", f"%{title}%", ''))

            results = cursor.fetchall()

            if not results:
                print("No matching data found for export.")
                return

            # Generate a unique timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            export_file_path = f"export_{location}_{title}_jobs_{timestamp}.csv"

            with open(export_file_path, 'w', newline='') as csvfile:
                fieldnames = ["id", "title", "company", "job_link", "location", "date_of_post"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for row in results:
                    # Extract only the relevant fields present in 'fieldnames'
                    row_to_write = {key: row[key] for key in fieldnames}
                    writer.writerow(row_to_write)

            print(f"Data exported to {export_file_path}")

        except Error as e:
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
