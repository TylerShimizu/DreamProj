import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from datetime import datetime
from api.models import Question, db

from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/documents"]
spreadsheet_id = "1nOYY4SqnoJ3il2QJ7vMOngiIXLBKX2pgskLNoDUdPC4"
range_name = ['Career Development!A1:Z', 'Community Engagement!A1:Z', 'Student-Athlete Performance!A1:Z', 'Personal Development, Misc.!A1:Z']
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

API_KEY = os.getenv("GOOGLE_API_KEY")

def main():
    try:
        data = {}
        id = 0
        id_and_questions = {}
        master_df = pd.DataFrame()
        for spread in range_name:
            service = build("sheets", "v4", developerKey=API_KEY)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=spreadsheet_id, range=spread)
                .execute()
            )
            #Values is a list of the rows in the spreadsheets
            
            values = result.get("values", [])

            if not values:
                print("No data found.")
                return
            else:
                df = pd.DataFrame(values)
                if not master_df.empty:
                    # Use the master_df's columns if it already has data
                    df.columns = master_df.columns[:-1]  # Exclude the 'Category' column
                else:
                    # Set the first row as headers and drop it from the data
                    df.columns = df.iloc[0]
                    df = df[1:]

                # Add the Category column
                df['Category'] = spread[:len(spread) - 5]

                # Append the new DataFrame to the master DataFrame
                master_df = pd.concat([master_df, df[1:]], ignore_index=True)

            
            #Making each entry in values to be a Questions object
            category = spread[:len(spread) - 5]
            sub_categories = defaultdict(list)
            for i in range(len(values)):
                temp = values[i]
                temp[4] = temp[4].split("->")
                sub = temp[4][0]

                q = Question.query.filter_by(level=temp[0], category=category, sub_category=sub, stem=temp[5], anchor=temp[7], method=temp[6]).first()

                if q:
        # Update last_updated timestamp
                    q.last_updated = datetime.now()
                else:
                    new = Question( 
                        level = temp[0], 
                        category = category, 
                        sub_category = temp[4][0], 
                        stem = temp[5], 
                        anchor = temp[7], 
                        method = temp[6]
                    )
                    db.session.add(new)
                    print("changed entry question #" + str(id))
                

                db.session.commit()

                ### Might change the categories to add what type of entry the question is wanting to make displaying the Questions and options easier when exporting to PDF ###
                # temp[7] = temp[7].split(";")
                # values[i] = Questions(id, temp[0], temp[3], category, sub, temp[5], temp[6], temp[7])
                # #sub = values[i].sub_cat.split("->")
                # sub_categories[sub].append(values[i])
                # id_and_questions[values[i].id] = values[i]
                # id += 1


            #Adding sheet into data dictionary with its sheet name as keys
            data[category] = sub_categories
        
        # Reset index of the final DataFrame for cleaner data
        master_df.reset_index(drop=True, inplace=True)
        master_df['id'] = master_df.index
        master_df['Sub-Category'] = master_df['Sub-Category'].str.split('->').str[0]
        return data, id_and_questions, master_df

    except HttpError as err:
        print(err)

if __name__ == "__main__":
  main()