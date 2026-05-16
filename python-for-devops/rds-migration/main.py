# python main.py --db-link 'postgresql://postgres:Admin1234@rds-migration.cvik8accw2tk.ap-south-1.rds.amazonaws.com:5432/postgres'
import argparse
import helper


def parse_args():
    parser = argparse.ArgumentParser(description='Migrate RDS database')
    parser.add_argument('--db-link', type=str, required=True, help='The link to the RDS database')
    args = parser.parse_args()
    return args

def main():
    parser = argparse.ArgumentParser(description='Migrate RDS database')
    parser.add_argument('--db-link', type=str, required=True, help='The link to the RDS database')
    args = parser.parse_args()
    helper.migrate_db(args.db_link)

if __name__ == "__main__":
    main()

# usage: python main.py --db-link 'postgresql://postgres:Admin1234@rds-migration.cvik8accw2tk.ap-south-1.rds.amazonaws.com:5432/postgres'