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

## Overview
- Use openAI chatGPT to tune our tables and queries
- Create a AWS Lex programmable chatbot so users have an interface in which to ask questions and get data responses
- Create a AWS Lambda function that takes a prompt as an input, sends it to openAI, and executes the SQL response against our database
- Connect our AWS Lambda function to the AWS Lex chatbot
- Integrate the AWS Lex with Slack, so users can talk to the chatbot and query for data right through their familiar Slack messaging app

## Use chatGPT to tune our natural language database prompt
This step can be a little bit time consuming, but a fun intro to the world of natural language SQL translation. Essentially we're going to give chatGPT an outline of our database schema, and then ask it a question to generate a SQL query we can run against the real database. Once we're happy with the results, we'll take the table data and create a single string that we'll send via API call.

- First create an account with openAI since we'll need to access chatGPT, and eventually API keys. You can create a free account at https://beta.openai.com/signup if you don't already have an account
- Look at your database schema and choose tables and columns that you'll want to query on. Put them in a text file that we can easily copy. Use the example below as the format:
```
Table: orders
+-----------------+----------+
Column Name = Type
+-----------------+----------+
id = int
created_at = datetime
updated_at = datetime
customer_id = int
+-----------------+----------+

Table: products
+-----------------+----------+
Column Name = Type
+-----------------+----------+
id = int
created_at = datetime
updated_at = datetime
description = text
name = string
+-----------------+----------+

Table: orders_products
+-----------------+----------+
Column Name = Type
+-----------------+----------+
id = int
created_at = datetime
updated_at = datetime
order_id = int
product_id = int
price = decimal
+-----------------+----------+

Table: users
+-----------------+----------+
Column Name = Type
+-----------------+----------+
id = int
created_at = datetime
updated_at = datetime
first_name = string
last_name = string
email = string
phone = string
type = string
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
  - What's the average amount of products in an order?

For example:
Query to chatGPT (using the example tables above):
```
Using only the below Postgresql tables, write a Postgresql query to give me the total price of the most recently created order.

<PASTE IN THE SQL TABLES HERE>
```

Response from chatGPT:
```sql
SELECT SUM(price)
FROM orders_products
WHERE order_id = (SELECT id FROM orders ORDER BY created_at DESC LIMIT 1);
```

- chatGPT should return some SQL code. You can copy and paste the code in to your terminal, or an app like Redash that is connected to your database to execute the SQL query against real data. **IMPORTANT** MAKE SURE YOUR USING A READ-ONLY DATABASE TO BE SAFE! NEVER EXECUTE UNVERIFIED QUERIES AGAINST CRITICAL PRODUCTION ENVIRONMENTS WITHOUT SAFEGUARDS IN PLACE!
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
[Amazon AWS Lex] is a chatbot service that we will use to ultimately let our users ask questions and get responses. AWS Lex will take our users question and send it over to a AWS Lambda function for processing, and then send the response back to the user.

TODO: Add steps to create Lex

## Create a AWS Lambda function to query openAI GPT
[Amazon AWS Lambda](https://aws.amazon.com/lambda/) allows us to run code in the cloud on a serverless platform, making setup easy and reliable. We'll use this as a mechanism to write our code which will take a user prompt and ask openAI GPT to generate a SQL query.
- Next, create an Amazon AWS account if you don't have one already. You can create an account at https://aws.amazon.com/
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
  - be sure to replace the openAI API key with your key
  - replace the `table_data` var with the SQL table string we created before based on the chatGPT test runs
  - replace the `database_query_url` var with the URL of your web server which will execute the SQL against your database and format a response
  - replace the `intent_name` with the name of the AWS Lex intent we created before, which is how the user will initiate a query to the openAI and the database. something like "openAiQuery" will work

## Connect the AWS Lambda function to AWS Lex
We now need to tell AWS Lex to use the Lambda function we created to fulfill it's intent.

TODO write steps

## Integrate AWS Lex with Slack
Since most users don't have access to AWS Lex directly, we should give them easy access via a Slack app. This will let users make natural language queries directly from their messaging app, and use the power of chatGPT to quickly get answers from the database!

TODO write steps to integrate Lex with Slack

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
