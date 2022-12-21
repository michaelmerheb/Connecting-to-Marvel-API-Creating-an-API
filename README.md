# Connecting-to-Marvel-API-Creating-an-API
This code is divided into two parts. In the first part we connect to the Marvel Developer Portal and retrieve the data specified below. In the second part we write the code to create an API to store the data retrieved and allow users to interact with them. 


# Part  1

We will complete the required steps to gain access to Marvel developer Portal. Once we do, we will write the code to complete the following tasks:

1. Provide a list of 30 Marvel characters
2. Retrieve the Ids for all the characters in your list (in str form)
3. Retrieve the total number of Events available for all the characters in your list (in integer form)
4. Retrieve the total number of Series available for all the characters in your list  (in integer form)
5. Retrieve the total number of Comics available for all the characters in your list (in integer form)
6. Retrieve the Price of the most expensive comic that the character was featured in or all the characters in your list (in float form and USD)
7. Store the data above in a pandas DataFrame called df containing exactly in the following columns: Character Name, Character ID, Total Available Events, Total Available Series, Total Available Comics, Price of the Most Expensive Comic. If a character is not featured in Events, Series or Comics the corresponding entry should be filled in with a None (of NoneType). If a character does not have a Price the corresponding entry should be filled in with a None (of NoneType).
8. Save df to a file called data.csv
