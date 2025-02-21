Workflow AI
Author: Parin Acharya
Submitted to: IBM Granite Hackathon

A comprehensive AI application built on top of IBM Granite to streamline business operations by analyzing existing workflows and suggestions improvements.

Workflow overview: 

- User sign in auth using Clerk (optional)

- Document upload and parsing: This will be done through the streamlit UI

- The document is saved to a database (Firebase) so that it can catch repeated uploads. The list of files available can be displayed on the UI

- Ability to create an business workflow analysis pipeline that: 

1) Extracts text from selected documents and converts to embeddings through an embedding model OR data from a chatbot conversation.
2) Embeddings are generated and stored in Pinecone Vector Store
3) These are passed to the IBM granite model for sentiment analysis and recommendations
4) the Streamlit UI is updated with picturesque visualizations and generated explanations
5) chat UI where user can ask a question or seek suggestions to their current workflow
6) this query is passed through the model again
7) after analysis, the details are saved in Firebase and can be viewed as a table of workflow score, generated suggestions, model used for analysis etc.

Social: linkedin.com/in/parinacharya
Lablab AI Project page: 

https://kellylougheed.medium.com/make-a-flask-app-with-a-nosql-database-using-firebase-612972ca3c4#:~:text=Setting%20up%20our%20database,%2C%20and%20press%20%E2%80%9CContinue.%E2%80%9D