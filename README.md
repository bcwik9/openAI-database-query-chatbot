# Use natural language prompts to direct openAI GPT to create SQL queries and retrieve data in your database
[openAI ChatGPT](https://chat.openai.com/chat) is an AI chatbot that has been in the news recently for it's popularity and functionality. This guide will allow you to leverage openAI GPT to generate SQL queries that we can run against a database to fetch data, simply by giving openAI GPT a description of the data we want to fetch. We'll then connect [Amazon AWS Lex](https://aws.amazon.com/lex/), another chatbot service, to a Slack app which will allow our end users to easily leverage the power of AI!

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
- Create a AWS Lambda function that takes a prompt as an input, sends it to openAI, and parses the SQL response
- Send the SQL query that openAI GPT gave us to the database which actually houses data, to get the actual data we want
- Connect the AWS Lamda function to AWS Lex, a programmable chatbot so users have an interface in which to ask questions and get data
- Integrate AWS Lex with Slack, so users can talk to the chatbot and query for data right through their familiar Slack app

## Create a AWS Lambda function to query openAI GPT
[Amazon AWS Lambda](https://aws.amazon.com/lambda/) allows us to run code in the cloud on a serverless platform, making setup easy and reliable. We'll use this as a mechanism to write our code which will take a user prompt and ask openAI GPT to generate a SQL query.
- First create an account with openAI since we'll need API keys from their site. You can create a free account at https://beta.openai.com/signup if you don't already have an account
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
- For your function code, replace it with the code in the Lambda function file in this repo
  - be sure to replace the openAI API key with your key
  - replace the `table_data` var with the SQL table string we created before based on the chatGPT test runs
  - replace the `database_query_url` var with the URL of your web server which will execute the SQL against your database and format a response

## Sources and references
- [Use a AWS Lambda function in AWS Lex v2](https://docs.aws.amazon.com/lexv2/latest/dg/lambda.html)
- [List of openAI GPT models available for use](https://beta.openai.com/docs/models/overview)
  - There's general models, and "Codex" models specifically meant for generating code
- [Examples of openAI GPT generating SQL queries from natural language prompts](https://beta.openai.com/examples/default-sql-translate)
- [Redash](https://redash.io/) is a helpful app that lets you connect directly to databases and other data stores, create and save queries, and visualize data. It's helpful for taking the SQL that ChatGPT generates and testing it out, or creating graphs and charts to share or monitor.
- [openAI AWS Lambda layer](https://github.com/erenyasarkurt/OpenAI-AWS-Lambda-Layer) is required to be able to use openAI GPT in a AWS Lambda function
- [Working with files in Ruby](https://www.rubyguides.com/2015/05/working-with-files-ruby/) is a helpful guide to take a file of text, and convert it to a single string (which is helpful to pass a lot of table data as text to openAI GPT as a prompt)
- [Guide to integrating AWS Lex with Slack](https://docs.aws.amazon.com/lexv2/latest/dg/deploy-slack.html)
