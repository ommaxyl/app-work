import boto3
import os
import mysql.connector

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_BUCKET_NAME ="my-static-s3-bucket-003"


RDS_ENDPOINT = 'your-rds-endpoint'
DB_USERNAME = 'your-username'
DB_PASSWORD = 'your-password'
DB_NAME = 'your-database-name'

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name='us-west-2'
)

dynamodb_client = session.client('dynamodb')
s3 = session.client('s3')

def save_to_s3(photo, photo_key, bucket_name=AWS_BUCKET_NAME):
    s3.upload_fileo(photo, bucket_name, photo_key)

def save_to_dynamodb(metadata):
    response = dynamodb_client.put_item(
        TableName='photo',
        Item={
            'user_id': {'N': str(metadata['user_id'])},
            'size': {'N': str(metadata['size'])},
            'type': {'S': metadata['type']},
            'creation_date': {'S': metadata['creation_date']}
        }
    )
def save_to_rds(data):
    try:
        connection = mysql.connector.connect(
            host=RDS_ENDPOINT,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()

        # Insert data into the database
        insert_query = "INSERT INTO employee (firstName, lastName, location, age, tech, profileImage) VALUES (%s, %s, %s, %s, %s, %s )"
        data_to_insert = (data['firstName'], data['lastName'], data['location'], data['age'],data['tech'], data['profileImage'])
        cursor.execute(insert_query, data_to_insert)


        # Commit the changes and close the connection
        connection.commit()
        cursor.close()
        connection.close()

        return True, "Data saved to the database successfully!"
    except mysql.connector.Error as err:
        return False, f"Error saving data: {err}"

if __name__ == "__main__":
    # Metadata of the object
    metadata = {
            'user_id': 1,
            'size': 1024,
            'type': 'image/jpeg',
            'creation_date': '2023-07-20',
            # Add more metadata attributes as needed
        }

    response= save_to_dynamodb(metadata)
    print(response)