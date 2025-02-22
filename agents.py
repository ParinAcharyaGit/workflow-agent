import requests

# you must manually set API_KEY below using information retrieved from your IBM Cloud account (https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-authentication.html?context=wx)
API_KEY = "vHKuy3n_Vbw8QctQOt5h4KZzheSWUqO10F1DV1zD9WH0"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]
print(mltoken)

headers = {
    'Authorization': f'Bearer + {mltoken}',
    'Content-Type': 'application/json',
}

payload_scoring = {"messages":[{"content":"Hi, help me understand step 1 in the business workflow provided. Use RAGQuery only.","role":"user"}]}

response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/528030d4-dac7-48b5-b39f-3776f6bb4ecc/ai_service?version=2021-05-01', json=payload_scoring,
 headers={'Authorization': 'Bearer ' + mltoken})
print("Scoring response")
print(response_scoring.json())