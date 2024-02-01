# sharepoint-rag-helper

The `sharepoint-rag-helper` project is a tool designed to support Retrieval Augmented Generation scenarios based on SharePoint Online content.
While focusing on PDF and DOCX documents now, it will be gradually extended to other types of content such as publishing pages.


## Prerequisites and deployment
There's still a bunch of manual steps, but I'll see to automate it peu à peu. So far I mostly run it locally for demo purposes but there's a Dockerfile to build a functional backend.

### Infrastructure 
Using the bicep template (make sure to adjust the parameters to your liking) you can create the following artifacts:
* Storage Account to keep the snapshots of PDF document pages (only some of them, identified as containing information that can be better processed by a visual model, such as technical drawings and tables)
* Azure AI Search to make document fragments discoverable using embeddings and full text search
* Azure WebPubSub to maintain communication with the user during the retrieval and indexing (as this operation can take some time) 

To run the template, 
1. Create a resource group in the location of your choice (all resources will be created in the same location)
2. execute the following Powershell script
```(az deployment group create -g [your precreated resource group] --template-file main.bicep | ConvertFrom-Json).properties.outputs.deployEnvironment.value | out-file -FilePath .env<code>```

It will give you a starter .env for your backend with the infra variables prefilled, so copy it to your backend and fill in the missing values.
The template is NOT creating the Azure Open AI instances and deployments (yet), please refer to your existing resources.
The template is also NOT creating the app registrations (yet), kindly refer to the next chapter to create them.

### App Registrations
* Single Page App for single tenant with a redirect URL pointing to your frontend deployment (http://localhost:3000 as long as you are experimenting locally)
    * pick your tenant ID and the client ID here
* API for single tenant with 
    * _delegated_ Graph permissions to Site.Read.All
    * a secret
    * some readable Application ID URI - pick the name, your scope to request tokens from the client app will be something like **api://your-sharepoint-rag-api/.default**
    * an exposed API with a scope such as access_as_user and
    * your SPA added as an authorized client application for the said scope

### Backend

In markdown, the best way to quote command line commands is by using backticks (`) to enclose the command. This will format the text as inline code. For multiline commands or code blocks, you can use triple backticks (```) before and after the command or code block. This will format the text as a code block.


Generate the .env (see "Infrastructure") or use the template pointing to your own precreated resources.
You can start with docker right away:

```
docker build . -t sharepoint-rag
docker run -p 8085:8085 sharepoint-rag</code>
```

Alternatively, create a python (mine is 3.11) venv, install the prerequisites and go python app.py.

To make certain everything is working properly, bring up your api OpenAPI UI (http://localhost:8085/docs for local deployments) and execute the 

### Frontend

In the frontend app folder
1. rename src/config.template.ts to src/config.ts and adjust the following values:
    * client ID of the frontend app registration
    * tenant ID
    * API base url for your frontend. For local deployments you can have is set to http://localhost:8085/api
    * scope of your backend api (see above)

1. run `npm start` in your frontend app folder

Access the application in your web browser at `http://localhost:3000`. Log in with your tenant's credentials.

