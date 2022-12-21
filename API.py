import datetime
import requests
import hashlib
import time
import pandas as pd
from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import create_access_token


#Q1:Creating an API that allows users to interact with the DataFrame generated in the Part 1 of the assignments
app = Flask(__name__)
api = Api(app)
bcrypt = Bcrypt(app) # Set up the Bcrypt extension
jwt = JWTManager(app) # Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "GPB10" #pass

#The below function will be called in the post request whenever we are accessing the 
#Marvel API and cross-checking/obtaining new character information to use in our data frame
def get_character_attributes(character_ID):
    private_key = "a0192c1b28f08ee214ef997b12df962854ac07a4"
    public_key = "094c7ab7bd000a68e4ec3afc8425fc5a"
    ts = time.time()
    st = str(ts)+private_key+public_key
    hash_result = hashlib.md5(st.encode('utf-8')).hexdigest()
    params = {'ts': ts, 'apikey': public_key, 'hash': hash_result}

    marvel_url = 'http://gateway.marvel.com/v1/public/characters/' + str(character_ID)
    response = requests.get(marvel_url, params=params)
       
    # Character ID doesn't exist
    if response.status_code != 200:
        return {'status': 400, 'response': "ERROR"}
    
    # Character ID exists
    else:
        character = response.json()['data']['results'][0]

        marvel_url = 'http://gateway.marvel.com/v1/public/characters/'+str(character_ID)+'/comics'
        list_of_comics = requests.get(marvel_url, params=params).json()['data']['results']

        price_list = []
        for comic in list_of_comics:
            list_of_prices = comic['prices']
            for comic_price in list_of_prices:
                price = comic_price['price']
                price_list.append(price)
        
        character['max_price'] = max(price_list)
        
        return {'status': 200, 'response': character}
    

#In order to protect unregistered users from manipulating the data frame, we must prompt them to
#sign up and log in before proceeding. The following block of code initiates that request.
#One function 'hash_password' and two classes 'SignUP' & 'LogIn' are created for that purpose.

def hash_password(password):
        return generate_password_hash(password).decode('utf8')

class SignUp(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help='Missing argument: email', required=True)
        parser.add_argument('password', type=str, help='Missing argument: password', required=True)
        args = parser.parse_args()  # parse arguments to dictionary

        # read our CSV
        try:
            data = pd.read_csv('users.csv')
        except FileNotFoundError:
            data = pd.DataFrame({'email':[], 'password':[]})
            data.to_csv('users.csv', index = False)

        if args['email'] in list(data['email']):
            return {'status': 409, 'response': f"{args['email']} already exists."}, 409
        else:
            # create new dataframe containing new values
            entry = pd.DataFrame({
                'email': [args['email']],
                'password': [hash_password(args['password'])]
            })
            
            # add entry to database
            data = data.append(entry, ignore_index=True)
            data.to_csv('users.csv', index=False)  # save back to CSV
            return {'status': 200, 'response': 'Successfully signed up'}, 200 # return data and 200 OK

class LogIn(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, help='Missing argument email', required=True)
        parser.add_argument('password', type=str, help='Missing argument password', required=True)
        args = parser.parse_args()  # parse arguments to dictionary

        # read our CSV
        data = pd.read_csv('users.csv')
        
        if args['email'] not in list(data['email']):
            return {'status': 401, 'response': f"Invalid email"}, 401
        else: 
            # look for password hash in database
            password = data.loc[data['email']==args['email'], 'password'][0]
            
            if bcrypt.check_password_hash(password, args['password']):
                expires = datetime.timedelta(hours=1)
                access_token = create_access_token(identity=str(data.loc[data['email']==args['email']].index[0]), expires_delta=expires)
                return {'status': 200, 'response': 'Successfully logged in', 'token': access_token}, 200 # return data and 200 OK
            else:
                return {'status': 401, 'response': f"Invalid password."}, 401


#Q2: Creating a resource called Characters
#Q3.1 & 3.2: Obtaining the whole DataFrame and information for a single or a list of entries
#Note: data type for Character ID is an integer now

class Characters(Resource):
    def get(self):

        parser = reqparse.RequestParser()
        parser.add_argument('Character ID', type = int, action='append', help="Missing Character ID", required = False)
        parser.add_argument('Character Name', type = str, action='append', help="Missing Character Name", required = False)
        
        args = parser.parse_args()
        data = pd.read_csv('Assignment_1_B10.csv')
        
        if (args['Character Name'] is None) and (args['Character ID'] is not None):
            if all(item in list(data['Character ID']) for item in args['Character ID']):
                data_sub = data.loc[data['Character ID'].isin(args['Character ID'])].to_dict(orient='records')
                return {'status': 200, 'response' : data_sub}
            else:
                return {'status': 404, 'response': 'The provided Character ID(s) is/are not in the database'}
        
        elif (args['Character Name'] is not None) and (args['Character ID'] is None):
            if all(item in list(data['Character Name']) for item in args['Character Name']):
                data_sub = data.loc[data['Character Name'].isin(args['Character Name'])].to_dict(orient='records')
                return {'status': 200, 'response' : data_sub}
            else:
                return {'status': 404, 'response': 'The provided Character Name(s) is/are not in the database'}
        
        else:
            data = data.to_dict(orient='records')
            return {'status': 200, 'response' : data}


#Q3.3:Adding a new character if and only if a unique Character ID is provided, and then the new entry is returned confirming successfull addition

    @jwt_required() 
    def post(self):
        parser = reqparse.RequestParser()
        
        parser.add_argument('Character Name', type=str, help='Missing argument Character Name', required=False)
        parser.add_argument('Character ID', type=int, help='Missing argument Character ID', required=True)
        parser.add_argument('Total Available Events', type=int, help='Missing argument Total Available Events', required=False)
        parser.add_argument('Total Available Series', type=int, help='Missing argument Total Available Series', required=False)
        parser.add_argument('Total Available Comics', type=int, help='Missing argument Total Available Comics', required=False)
        parser.add_argument('Price of the Most Expensive Comic', type=float, help='Missing argument Price of the Most Expensive Comic', required=False)
        
        args = parser.parse_args()  # parse arguments to dictionary

        data = pd.read_csv('Assignment_1_B10.csv')# read CSV

        if args['Character ID'] in list(data['Character ID']):
            return {'status': 409, 'response': f"'{args['Character ID']}' already exists."}, 409
        
        # add character
        else: 
            if args['Character Name'] is not None and args['Character ID'] is not None:
                entry = pd.DataFrame({
                    'Character Name': [args['Character Name']],
                    'Character ID': [args['Character ID']],
                    'Total Available Events': [args['Total Available Events']],
                    'Total Available Series': [args['Total Available Series']],
                    'Total Available Comics': [args['Total Available Comics']],
                    'Price of the Most Expensive Comic': [args['Price of the Most Expensive Comic']]})# create new df entry
            else:
                response = get_character_attributes(args['Character ID']) #function defined earlier to avoid spaghetti code
                
                if response['status'] == 400:
                    return {'status': 400, 'response': f"'{args['Character ID']}' doesn't exists in Marvel's API"}, 400
                else:
                    character = response['response']
                    entry = pd.DataFrame({
                        'Character Name': [character['name']],
                        'Character ID': [args['Character ID']],
                        'Total Available Events': [character['events']['available']],
                        'Total Available Series': [character['series']['available']],
                        'Total Available Comics': [character['comics']['available']],
                        'Price of the Most Expensive Comic': [character['max_price']]})

            data = data.append(entry, ignore_index=True) # add entry to database
            data.to_csv('Assignment_1_B10.csv', index=False)  # save back to CSV
            entry = data.loc[data['Character ID']==args['Character ID']] # retrieve entry with productId
            entry = entry.to_dict(orient='records') # convert dataframe to dict
            return {'status': 200, 'response': entry}, 200 # return data and 200 OK

#Q3.5: deleting characters based on Character ID or Character Name, and handling errors for wrong inputs
        
    @jwt_required()        
    def delete(self):
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('Character ID', type=int, help='Missing argument Character ID', required=False)  # add Character Id arg
        parser.add_argument('Character Name', type=str, help='Missing argument Character Name', required=False)  # add Character Name arg
        args = parser.parse_args()  # parse arguments to dictionary

        data = pd.read_csv('Assignment_1_B10.csv') # read CSV

        if args['Character ID'] is not None:
            if args['Character ID'] in list(data['Character ID']):
                data = data[data['Character ID'] != args['Character ID']] # remove data entry matching given Character ID
                data.to_csv('Assignment_1_B10.csv', index=False) # save back to CSV
                data = data.to_dict(orient='records') # convert data to dict
                return {'status': 200, 'response': data}, 200 # return data and 200 OK
            else:
                return {'status': 404, 'response': f"Incorrect value {args['Character ID']} for Character ID."}, 404
        elif args['Character Name'] is not None:
            if args['Character Name'] in set(data['Character Name']):
                data = data[data['Character Name'] != args['Character Name']] # remove data entry matching given Character Name
                data.to_csv('Assignment_1_B10.csv', index=False) # save back to CSV
                data = data.to_dict(orient='records') # convert data to dict
                return {'status': 200, 'response': data}, 200 # return data and 200 OK
            else:
                return {'status': 404, 'response': f"Incorrect value {args['Character Name']} for Character Name."}, 404
        else:
            return {'status': 404, 'response': f"Missing argument Character ID or Character Name."}, 404
        

#Q2: Routing the characters resource to url and endpoint
api.add_resource(Characters, '/characters', endpoint = 'characters')
api.add_resource(SignUp, '/signup', endpoint='signup')
api.add_resource(LogIn, '/login', endpoint='login')

if __name__ == '__main__':
    app.run(debug=True)