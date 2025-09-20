# Feature: example


## Scenario 1

1. Use context "context_default"



2. Process operation "handle"



3. External API request in service "github" method:get path:/ 
Response content: {'name': 'name'}
Response status: 200



4. External API request in service "nationalize" method:post path:/ with query params: {'name': 'kate'}
Response content: {'country': [{'country_id': 'GB', 'probability': 0.67}, {'country_id': 'US', 'probability': 0.23}, {'country_id': 'CA', 'probability': 0.05}, {'country_id': 'AU', 'probability': 0.02}, {'country_id': 'NZ', 'probability': 0.01}, {'country_id': 'IE', 'probability': 0.01}, {'country_id': 'ZA', 'probability': 0.01}], 'name': 'kate'}
Response status: 200




## Scenario 2

1. Use context "context_default"



2. Process operation "handle"



3. External API request in service "github" method:get path:/ 
Response content: {'name': 'name'}
Response status: 200



4. External API request in service "nationalize" method:post path:/ with query params: {'name': 'kate'}
Response status: 404



5. External API request in service "ipinfo" method:get path:/161.185.160.93/geo 
Response content: {'city': 'London', 'country': 'GB', 'loc': '51.5074,-0.1278', 'postal': 'SW1A', 'region': 'England', 'timezone': 'Europe/London'}
Response status: 200




## Scenario 3

1. Use context "context_default"



2. Process operation "handle"



3. External API request in service "github" method:get path:/ 
Response content: {'name': 'name'}
Response status: 200



4. External API request in service "nationalize" method:post path:/ with query params: {'name': 'kate'}
Response status: 404



5. External API request in service "ipinfo" method:get path:/161.185.160.93/geo 
Response status: 404




## Scenario 

1. Use context "context_default"



2. Process operation "handle"



3. External API request in service "github" method:get path:/ 
Response content: {'name': 'name'}
Response status: 200



4. External API request in service "nationalize" method:post path:/ with query params: {'name': 'kate'}
Response status: 404



5. External API request in service "ipinfo" method:get path:/161.185.160.93/geo 
Response status: 500




## Scenario 

1. Use context "context_default"



2. Process operation "handle"



3. External API request in service "github" method:get path:/ 
Response content: {'name': 'name'}
Response status: 200



4. External API request in service "nationalize" method:post path:/ with query params: {'name': 'kate'}
Response status: 500




## Scenario 4

1. Use context "context_default"



2. Process operation "handle"



3. External API request in service "github" method:get path:/ 
Response status: 404



4. External API request in service "nationalize" method:post path:/ with query params: {'name': 'kate'}
Response content: {'country': [{'country_id': 'GB', 'probability': 0.67}, {'country_id': 'US', 'probability': 0.23}, {'country_id': 'CA', 'probability': 0.05}, {'country_id': 'AU', 'probability': 0.02}, {'country_id': 'NZ', 'probability': 0.01}, {'country_id': 'IE', 'probability': 0.01}, {'country_id': 'ZA', 'probability': 0.01}], 'name': 'kate'}
Response status: 200




## Scenario 

1. Use context "context_default"



2. Process operation "handle"



3. External API request in service "github" method:get path:/ 
Response status: 500



4. External API request in service "nationalize" method:post path:/ with query params: {'name': 'kate'}
Response content: {'country': [{'country_id': 'GB', 'probability': 0.67}, {'country_id': 'US', 'probability': 0.23}, {'country_id': 'CA', 'probability': 0.05}, {'country_id': 'AU', 'probability': 0.02}, {'country_id': 'NZ', 'probability': 0.01}, {'country_id': 'IE', 'probability': 0.01}, {'country_id': 'ZA', 'probability': 0.01}], 'name': 'kate'}
Response status: 200



