import os

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow
import pandas as pd
from datetime import datetime
from api.models import Question, db

from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/documents"]
spreadsheet_id = "1nOYY4SqnoJ3il2QJ7vMOngiIXLBKX2pgskLNoDUdPC4"
range_name = ['Career Development!A2:Z', 'Community Engagement!A1:Z', 'Student-Athlete Performance!A1:Z', 'Personal Development, Misc.!A1:Z']
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

API_KEY = os.getenv("GOOGLE_API_KEY")
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["http://localhost:5000/callback"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=[
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file"
    ]
)

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
                    temp[7] = temp[7].split(";")
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

def create_doc(questions, creds):
    try:
        service = build("docs", "v1", credentials=creds)
        title = {
            "title": "Sample Survey"
        }
        doc = service.documents().create(body=title).execute()
        document_id = doc.get('documentId')

        requests = []
        current_index = 1

        for _, question in questions.iterrows():
            # Insert the question text
            print(question)
            print(type(question))
            if question is not None:
                requests.append({
                    "insertText": {
                        "location": {
                            "index": current_index
                        },
                        "text": question["Item Stem"] + "\n"
                    }
                })
                current_index += len(question["Item Stem"]) + 1

                anchors = question["Anchors"].split(";")
                if len(anchors) > 0:
                    for choice in anchors:
                        requests.append({
                            "insertText": {
                                "location": {
                                    "index": current_index
                                },
                                "text": "\t" + choice + "\n"
                            }
                        })
                        current_index += len(choice) + 2
        requests.append({
            'createParagraphBullets': {
                'range': {
                    'startIndex': 1,
                    'endIndex': current_index
                },
                'bulletPreset': 'NUMBERED_DECIMAL_ALPHA_ROMAN_PARENS',
            }
        })

        result = service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

        return document_id

    except HttpError as err:
        print(f"An error occurred: {err}")


if __name__ == "__main__":
  main()