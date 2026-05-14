
1. csv data ->  transformation -> db
2. s3 upload -> file process -> do something meaningfuk
3. cost useage report
4. unused resourecsdeleteion
5. email user 
6. start/stop




s3 as trigger
- multiple processing based on the file
- send email 
-> S3 will need invoke lambda permission
-> invocation based on put event on a certain path. 



python need to deal with certain things

python need something that work with database -> psycopg-binary 
 db hostname, cred, dbname 

 n/w should allow the lanbda to talk to rds 




 user: postgres
 pass: Admin1234
 db_name: tradedb





 docker run -td \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_PROFILE="default" \
  -e AWS_DEFAULT_REGION="ap-south-1" \
  rds-migration:latest


  docker run -td \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  -e AWS_DEFAULT_REGION="ap-south-1" \
  rds-migration:latest


docker logs -f 03f1be038362f5ec910e9e981738cb2d7b090d41e727ebec24f0db90ec6229e2