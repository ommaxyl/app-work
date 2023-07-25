from flask import Flask, render_template, request
import boto3
from botocore.exceptions import ClientError
import mysql.connector
import jsonify

app = Flask(__name__)

# Replace these constants with your RDS credentials and database information
RDS_ENDPOINT = 'my-database.cvlboroeob4n.us-east-1.rds.amazonaws.com'
DB_USERNAME = 'admin'
DB_PASSWORD = 'password2'
DB_NAME = 'employee'

# Replace these constants with your AWS credentials and S3 bucket name
AWS_ACCESS_KEY_ID = 'AKIAWZTCHYL32YWKVAK6'
AWS_SECRET_ACCESS_KEY = 'NePlbuKvqdK1vdNPn0AMTPI4d8GXSGuezk0lQL0v'
AWS_BUCKET_NAME = 'my-practice-bucket-capstone'
DYNAMODB_TABLE_NAME = 'my-capstone-practice-table'


def save_to_rds(data, s3_url):
    try:
        connection = mysql.connector.connect(
            host=RDS_ENDPOINT,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()

        # Insert data into the database
        insert_query = "INSERT INTO employee (firstName, lastName, location, salary, email, profileImage) VALUES (%s, %s, %s, %s, %s, %s )"
        data_to_insert = (data['firstName'], data['lastName'], data['location'], data['salary'], data['email'], s3_url)
        cursor.execute(insert_query, data_to_insert)

        # Commit the changes and close the connection
        connection.commit()
        cursor.close()
        connection.close()

        return True, "Data saved to the database successfully!"
    except mysql.connector.Error as err:
        return False, f"Error saving data: {err}"

def save_to_s3(profileImage, photo_filename):
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        # Upload the file to S3
        s3.upload_fileobj(profileImage, AWS_BUCKET_NAME, photo_filename)

        return True, "Photo uploaded to S3 successfully!"
    except ClientError as e:
        return False, f"Error uploading photo to S3: {e}"

def save_metadata_to_dynamodb(metadata):
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name='us-east-1'
        )
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)

        # Put the metadata item to DynamoDB
        response = table.put_item(Item=metadata)

        return True, "Metadata saved to DynamoDB successfully!"
    except ClientError as e:
        return False, f"Error saving metadata to DynamoDB: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = {
            'firstName': request.form['firstname'],
            'lastName': request.form['lastname'],
            'location': request.form['location'],
            'salary': request.form['salary'],
            'email': request.form['email'],
            'profileImage': request.files['profileImage']
        }

        # Save employee data to RDS
        #saved_to_rds, rds_message = save_to_rds(data, s3_url)

        # Save employee photo to S3
        profileImage = request.files['profileImage']
        if profileImage:
            photo_filename = profileImage.filename
            saved_to_s3, s3_message = save_to_s3(profileImage, photo_filename)

            # If the photo was successfully saved to S3, save data to RDS
            if saved_to_s3:
                # Get the S3 URL of the uploaded photo
                s3_url = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{photo_filename}"

                # Save employee data to RDS, passing the S3 URL as an argument
                saved_to_rds, rds_message = save_to_rds(data, s3_url)
            else:
                saved_to_rds = False
                rds_message = "Error saving data to RDS: Photo not uploaded to S3."
        else:
            saved_to_s3 = False
            s3_message = "No photo provided."
            saved_to_rds = False
            rds_message = "Error saving data to RDS: Photo not uploaded."

        # Save metadata to DynamoDB
        metadata = {
            'user_id': 1,  # Replace with a unique user ID or generate one dynamically
            'size': 200,  # Assuming you want to save the photo size in bytes
            'type': profileImage.content_type,
            'creation_date': '2023-07-20',  # Replace with the actual creation date
            # Add more metadata attributes as needed
        }
        saved_to_dynamodb, dynamodb_message = save_metadata_to_dynamodb(metadata)

        if saved_to_rds and saved_to_s3 and saved_to_dynamodb:
            return "Data, photo, and metadata saved successfully!"
        else:
            return f"Error: {rds_message}\n{('' if saved_to_s3 else 'S3 Error: ')}{s3_message}\n{('' if saved_to_dynamodb else 'DynamoDB Error: ')}{dynamodb_message}"

    return render_template('index.html')


@app.route('/employee', methods=['GET', 'POST'])
def employeePage():
    employee = get_employee_data(1)
    return render_template('employee_info.html', employee = employee)


def get_employee_data(id):
    try:
        connection = mysql.connector.connect(
            host=RDS_ENDPOINT,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()

        # Select data from the database
        select_query = f"SELECT * FROM employee WHERE id = {id}"
        cursor.execute(select_query)
        employee_data = cursor.fetchall()

        # Close the connection
        cursor.close()
        connection.close()

        # Return the employee data as a JSON response
        return jsonify(employee_data)

    except mysql.connector.Error as err:
        return jsonify({'error': f"Error retrieving data: {err}"})

if __name__ == '__main__':
    app.run(debug=True)
