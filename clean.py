import os
import sys
sys.path.append("refine.py")
import refine
import io
import csv
import pandas as pd
import sqlite3


def main(csv_file = 'data.csv', json_file = 'data.json', project_name = 'tax', db_name = 'tax.db', out_file = 'cleaned_data.csv'):

  #Concatenating the tax files

  try:
      os.stat(csv_file)
  except:
      os.system('cat *.csv > {}'.format(csv_file))
      


  # Interacting with OpenRefine HTTP API using a readymade JSON recipe

  r = refine.Refine()
  p = r.create_new_project(csv_file, project_name)
  p.apply_operations(json_file)
  response = p.export_rows()
  p.delete_project()


  # Creating the SQL Database 

  con = sqlite3.connect(db_name)
  c = con.cursor()
  c.execute('''CREATE TABLE IF NOT EXISTS TaxCert(Business_Acc_No int NOT NULL PRIMARY KEY,
                                                  Business_Name text UNIQUE,
                                                  Ownership_Type text,
                                                  Address text,
                                                  City text,
                                                  Zip int,
                                                  State text,
                                                  Phone_No int,
                                                  Owner_Name text,
                                                  Creation_Date text,
                                                  Start_Date text,
                                                  Exp_Date text,
                                                  NAICS int,
                                                  Business_Description text);''')

  csv_file = csv.DictReader(io.StringIO(response.decode('utf-8')))
  to_db = [(i['Business_Acc_No'],
            i['Business_Name'],
            i['Ownership_Type'],
            i['Address'],
            i['City'],
            i['Zip'],
            i['State'],
            i['Phone_No'],
            i['Owner_Name'],
            i['Creation_Date'],
            i['Start_Date'],
            i['Exp_Date'],
            i['NAICS'],
            i['Business_Description']) for i in csv_file]

  c.executemany('INSERT OR IGNORE INTO TaxCert VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);', to_db)

  # Imputing the empty values as Null in the table

  col_names = ['Business_Acc_No',
               'Business_Name',
               'Ownership_Type',
               'Address',
               'City',
               'Zip',
               'State',
               'Phone_No',
               'Owner_Name',
               'Creation_Date',
               'Start_Date',
               'Exp_Date',
               'NAICS',
               'Business_Description']

  for col in col_names:
      c.execute('UPDATE TaxCert SET {} = NULL WHERE {} = "";'.format(col,col))




  ## Testing for IC Violations

  # NOTE: The Null Values are left as they are. They can be changed depending on the use case

  # Making sure we are using only San Diego data
  c.execute('DELETE FROM TaxCert WHERE (City IS NOT NULL AND State IS NOT NULL) AND (City != "San Diego" OR State != "CA");')

  # Making sure the Zip Codes are valid
  c.execute('UPDATE TaxCert SET Zip = NULL WHERE Zip IS NOT NULL AND (LENGTH(Zip) != 9 AND LENGTH(Zip) != 5);')
  c.execute('UPDATE TaxCert SET Zip = SUBSTR(CAST(Zip AS TEXT), 1, 5) || "-" || SUBSTR(CAST(Zip AS TEXT), 4, 9) WHERE LENGTH(Zip) = 9;')

  # Making sure the Phone Numbers are valid
  c.execute('UPDATE TaxCert SET Phone_No = NULL WHERE Phone_No IS NOT NULL AND (TYPEOF(Phone_No) != "integer" OR LENGTH(Phone_No) != 10);')

  # Creation_Date or Start_Date cannot be later than Exp_Date
  c.execute('DELETE FROM TaxCert WHERE DATE(Creation_Date) > DATE(Exp_Date);')
  c.execute('DELETE FROM TaxCert WHERE DATE(Start_Date) > DATE(Exp_Date);')

  #Identifying the expired TaxCertificates
  c.execute('SELECT Business_Acc_No FROM TaxCert WHERE DATE(Exp_Date) < DATE("now");')
  print('Expired Businesses are...')
  print(c.fetchall())
  con.commit()


  #Exporting the cleaned data into a csv

  data = pd.read_sql_query('SELECT * FROM TaxCert', con)
  data.to_csv(out_file, index=False)

if __name__ == '__main__':
  main()

