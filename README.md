# Use natural language prompts to direct openAI GPT to create SQL queries and retrieve data in your database
[openAI ChatGPT](https://chat.openai.com/chat) is an AI chatbot that has been in the news recently for it's popularity and functionality. This guide will allow you to utilize openAI GPT to generate SQL queries that we can run against a database to fetch data, simply by giving openAI GPT a description of the data we want to fetch. chatGPT is awesome since it can infer relationships and other quirks about our SQL tables automatically! We'll then connect [Amazon AWS Lex](https://aws.amazon.com/lex/), another chatbot service, to a Slack app which will allow our end users to easily leverage the power of AI!

Some technologies we'll use:
- [openAI GPT-3](https://openai.com/api/): A powerful AI chatbot good at performing natural language tasks
- [Amazon AWS Lambda](https://aws.amazon.com/lambda/): Run code in the cloud without a server
- [Amazon AWS Lex](https://aws.amazon.com/lex/): A customizable, conversational AI chatbot
- [Slack](https://slack.com/): An instant messaging platform

## Requirements
What you'll need:
- SQL database with your data
- A web server endpoint that takes a SQL query string, executes it against your database, and returns the results as JSON
- An Amazon AWS account if you don't have one already. You can create an account at https://aws.amazon.com/
- An openAI account for GPT API keys. You can create an account at https://beta.openai.com/signup

## Overview
- Use openAI chatGPT to tune our tables and queries
- Create a AWS Lex programmable chatbot so users have an interface in which to ask questions and get data responses
- Create a AWS Lambda function that takes a prompt as an input, sends it to openAI, and executes the SQL response against our database
- Connect our AWS Lambda function to the AWS Lex chatbot
- Integrate the AWS Lex with Slack, so users can talk to the chatbot and query for data right through their familiar Slack messaging app

## Use chatGPT to tune our natural language database prompt
This step can be a little bit time consuming, but a fun intro to the world of natural language SQL translation. Essentially we're going to give chatGPT an outline of our database schema, and then ask it a question to generate a SQL query we can run against the real database. Once we're happy with the results, we'll take the table data and create a single string that we'll send via API call.

- First create an account with openAI since we'll need to access chatGPT, and eventually API keys. You can create a free account at https://beta.openai.com/signup if you don't already have an account
- Look at your database schema and choose tables and columns that you'll want to query on. Put them in a text file that we can easily copy. I'm using https://www.w3schools.com/sql/trysql.asp?filename=trysql_asc as an example database/schema that we can query against. Use the example below as the format:
```
Table: Orders
+-----------------+----------+
Column Name = Type
+-----------------+----------+
OrderID	 = int
OrderDate = datetime
CustomerID = int
+-----------------+----------+

Table: Products
+-----------------+----------+
Column Name = Type
+-----------------+----------+
ProductID = int
ProductName = string
Price = decimal
+-----------------+----------+

Table: OrderDetails
+-----------------+----------+
Column Name = Type
+-----------------+----------+
OrderDetailID = int
OrderID = int
ProductID = int
+-----------------+----------+

Table: Customers
+-----------------+----------+
Column Name = Type
+-----------------+----------+
CustomerID = int
ContactName = string
Address = string
City = string
PostalCode = string
Country = string
+-----------------+----------+
```
- open up chatGPT and paste the following in the chat box:
```
Using only the below Postgresql tables, write a Postgresql query to <ENTER A DESCRIPTION OF SOME DATA YOU WOULD LIKE TO RETRIEVE>.

<PASTE IN YOUR SQL TABLES HERE>
```
- Some example queries to try:
  - Give me all the customer names who had orders created in 2022
  - Show the top 5 product names that are most commonly purchased
  - What's the average number of unique products in an order?

For example:
Query to chatGPT (using the example tables above):
```
Using only the below Postgresql tables, write a Postgresql query to give me the total price of the most recently created order.

<PASTE IN THE SQL TABLES HERE>
```

Response from chatGPT:
```sql
SELECT SUM(p.Price) as TotalPrice
FROM Orders o
JOIN OrderDetails od ON o.OrderID = od.OrderID
JOIN Products p ON od.ProductID = p.ProductID
WHERE o.OrderID = (SELECT MAX(OrderID) FROM Orders)
```

- chatGPT should return some SQL code. You can copy and paste the code in to your terminal, or an app like Redash that is connected to your database to execute the SQL query against real data. **IMPORTANT** MAKE SURE YOUR USING A READ-ONLY DATABASE TO BE SAFE! NEVER EXECUTE UNVERIFIED QUERIES AGAINST CRITICAL PRODUCTION ENVIRONMENTS WITHOUT SAFEGUARDS IN PLACE!
  - If using the example database above, you can copy/paste the SQL in to the page at https://www.w3schools.com/sql/trysql.asp?filename=trysql_asc and run it to see results
- Keep tuning your queries and tables/columns you give chatGPT until you're happy with the queries you can make against your data. Remember, the more tables you include, the more questions you can answer. On the flip side, it makes it harder and more expensive for chatGPT to interpret.
- Once happy, take your tables and convert them to a single string that we'll end up pasting in to our AWS Lambda function later. I accomplished this using Ruby:
```ruby
file = File.open("YOUR_TABLES_FILE.txt")
file.read

# You should get an escaped string that looks something like:
# "user1\nuser2\nuser3\n......"
```
- Copy this tables string down, as we'll need it in our AWS Lambda function

## Create a AWS Lex chatbot
[Amazon AWS Lex](https://aws.amazon.com/lex/) is a chatbot service that we will use to ultimately let our users ask questions and get responses. AWS Lex will take our users question and send it over to a AWS Lambda function for processing, and then send the response back to the user.

- Go to Amazon Lex
- Click "Create Bot" to create a new bot
  - Select "Create a blank bot" for Creation Method
  - Enter a name for the bot
  - For IAM Permissions, click Create new role with basic permissions (unless you have an existing role)
  - For COPPA select "No"
  - Click Next
  - On the next page, select a voice for the bot to use
  - Click Done
- If it didn't create a new intent for you, select Intents from the lefthand menu and click Add intent -> Add empty intent
  - Scroll down to the "Intent details" section and enter a name for your intent, such as "SqlQuery". Write it down as we'll need this later
  - Scroll down to the "Sample utterances" section, and add a phrase such as "Find data" or "Query SQL" or something that will let Lex know we're ready to perform a SQL query. Click "Add utterance"
  - Scroll down to the "Slots" section and click "Add slot"
    - Make sure the slot is required
    - Enter a name such as "sql_query"
    - Enter "FreeFormInput" for the slot type
    - For prompts, enter something like "What is your query?" to prompt the user the start entering their query
  - Scroll down to the "Fulfillment" section
    - Expand the "On successful fulfillment" panel and click "Advanced options"
    - Under "Fulfillment Lambda code hook" make sure "Use a Lambda function for fulfillment" is checked
    - Click the "Update options" button at the bottom to save
  - Scroll back up to the "Initial response" section
    - Click on "Advanced options"
    - Find the "Dialog code hook" panel, and click "Lambda dialog code hook" to expand it
    - Make sure "Invoke Lambda function" is checked
    - Click "Advanced options"
    - Find the "Success response" panel and click the "Set values" section to expand it
    - Set "Next step in conversation" to "Elicit a slot"
    - For the slot, select the slot we created before from the dropdown (in our example it's "sql_query")
    - Click the "Update options" button at the bottom
    - Click "Update options" again
  - Click on "Save intent" at the bottom
- In the top right corner, click the Build button to build your bot. This will take a little bit on time.
- Proceed to the next step

## Create a webhook to return actual results from your database
**IMPORTANT** MAKE SURE YOUR USING A READ-ONLY DATABASE TO BE SAFE! NEVER EXECUTE UNVERIFIED QUERIES AGAINST CRITICAL PRODUCTION ENVIRONMENTS WITHOUT SAFEGUARDS IN PLACE!

OpenAI GPT can't run actual SQL queries against your database (nor would you want it to for data privacy concerns). Instead, we need to take the suggested SQL query that openAI GPT gives us, and hand it off to our webserver (or whatever service you'd like to use) for running the SQL query and returning formatted results.

How you decide to handle this is up to you. I typically run a rails server that I can authenticate queries from Lex using a basic key that's passed in as a param, and the webserver checks the key to make sure it's valid. If it isn't valid, then it just exits since it isn't a valid user requesting a query.

I've previously utilized a Rails server to handle this (example below):
- Create a new route/controller method that will take a SQL query as text, and a text auth key
- Check the text auth key to make sure the key being passed in params matches what we expect. If it doesn't, ignore the request or throw and error
- Once we verify the query is from a valid source, execute the SQL query
- Format the results of the SQL query. In my case, I had the webserver generate a Google Sheets spreadsheet and save the URL of the spreadsheet
- Return the results as JSON (in my case I returned a URL of the google spreadsheet)

## Create a AWS Lambda function to query openAI GPT for SQL and send that SQL to your webserver for processing
[Amazon AWS Lambda](https://aws.amazon.com/lambda/) allows us to run code in the cloud on a serverless platform, making setup easy and reliable. We'll use this as a mechanism to write our code which will take a user prompt and ask openAI GPT to generate a SQL query.
- Before we create our AWS Lambda function, we'll need to download a Lambda layer environment that supports openAI. This will allow us to use the openAI functionality in our Lambda function. Head to https://github.com/erenyasarkurt/OpenAI-AWS-Lambda-Layer and download the latest release zip.
- Now we'll add the layer we just downloaded to AWS. Go to the Amazon AWS web console home page. Find and click on the [AWS Lambda service](https://aws.amazon.com/lambda/)
- Click on Layers -> Create layer
  - give the layer a name, such as "openAI"
  - upload the openAI layer zip file we downloaded before
  - select all the available architectures (not sure if this is correct)
  - for the Compatible runtimes, select the same version of Python that came with the openAI layer zip we uploaded
  - click Create
- On the AWS Lambda homepage, click "Create function" to start creating a new Lambda function
  - select "From scratch"
  - enter a name for your function, such as "openAIQuery"
  - for the Runtime, select the same version of Python that we selected before
  - for the Architecture, select x86_64
  - click Create function
- On the newly created function page, scroll down til you see the Layers panel. Click on "Add a layer"
  - select Custom layers, and select the openAI layer we created before
  - select the latest version (there's probably only one option available)
  - click Add
- For your function code, replace it with the code in the Lambda function file in this repo: [lambda_function.py](https://github.com/bcwik9/openAI-database-query-chatbot/blob/main/lambda_function.py)
  - repalce the `openai.api_key` var with your openAI API key
  - replace the `table_data` var with the SQL table string we created before based on the chatGPT test runs
  - replace the `database_query_url` var with the URL of your web server which will execute the SQL against your database and format a response
  - replace the `intent_name` with the name of the AWS Lex intent we created before, which is how the user will initiate a query to the openAI and the database. We used "SqlQuery" as the example intent name before.
- Click the "Configuration" tab
  - Click on "General Configuration"
  - Click the Edit button
  - Change the Timeout to something like 45 seconds. Otherwise the function will probably error out since it takes time for openAI GPT to formulate a response
  - Click the Save button
- Go back to the "Code"T tab and click "Deploy" at the top to deploy your Lambda function for usage
- Now let's create a new test to verify your lambda function is working properly. There should be a "Test" button at the top with a dropdown arrow. Select the dropdown and click "Configure test event"
  - Select "Create new event"
  - Enter a name for your event, such as "SimpleQuery"
  - Select Private for "Event sharing settings"
  - Use the below template for your test. It's essentially simulating a query in the format that Lex will give. You can change the "originalValue" text to a different test SQL query if you want:
  - ```
    {
      "sessionState": {
        "intent": {
          "slots": {
            "sql": {
              "value": {
                "originalValue": "find the top five customer names with the most number of orders"
              }
            }
          }
        }
      }
    }
    ```
  - Click Save at the bottom
  - Now click the Test button again to run the test. You should see some output from what will be returned to the user.
- Once you verify your Lambda function is working, move on to the next step

## Connect the AWS Lambda function to AWS Lex
We now need to tell AWS Lex to use the Lambda function we created to fulfill it's intent.

- Go to AWS Lex
- In the lefthand menu, select Bots and then the bot you created before
- Click on intents, then click the "Test" button in the top left hand corner (press "Build" if you need to build the bot). It should pop open a chat window
- Click on the Gear icon in the top right side of the chat window
- Expand the "Lambda function" panel
  - For the Source, select the Lambda function we created before
  - For version, select the latest version
  - Click the Save button at the bottom
- Now you're ready to test your bot!
  - Enter the phrase we created for the Lex utterance (in our example it's "Find data") and send it
  - The bot should respond with our Slot prompt (in this example "What is your query?")
  - Enter your SQL question (such as "give me the total price of the most recently created order")
  - The bot should send your text over to the Lambda function we created, and show you actual data from your database!

## Integrate AWS Lex with Slack
Since most users don't have access to AWS Lex directly, we should give them easy access via a Slack app. This will let users make natural language queries directly from their messaging app, and use the power of chatGPT to quickly get answers from the database!

[See the guide to integrating AWS Lex with Slack](https://docs.aws.amazon.com/lexv2/latest/dg/deploy-slack.html)

## Sources and references
- [Use a AWS Lambda function in AWS Lex v2](https://docs.aws.amazon.com/lexv2/latest/dg/lambda.html)
- [List of openAI GPT models available for use](https://beta.openai.com/docs/models/overview)
  - There's general models, and "Codex" models specifically meant for generating code
- [Examples of openAI GPT generating SQL queries from natural language prompts](https://beta.openai.com/examples/default-sql-translate)
  - It seems the best way to specify a table/columns may be: `# Table albums, columns = [AlbumId, Title, ArtistId]`. See https://platform.openai.com/docs/guides/code/best-practices
- [Redash](https://redash.io/) is a helpful app that lets you connect directly to databases and other data stores, create and save queries, and visualize data. It's helpful for taking the SQL that ChatGPT generates and testing it out, or creating graphs and charts to share or monitor.
- [openAI AWS Lambda layer](https://github.com/erenyasarkurt/OpenAI-AWS-Lambda-Layer) is required to be able to use openAI GPT in a AWS Lambda function
- [Working with files in Ruby](https://www.rubyguides.com/2015/05/working-with-files-ruby/) is a helpful guide to take a file of text, and convert it to a single string (which is helpful to pass a lot of table data as text to openAI GPT as a prompt)
- [Guide to integrating AWS Lex with Slack](https://docs.aws.amazon.com/lexv2/latest/dg/deploy-slack.html)
