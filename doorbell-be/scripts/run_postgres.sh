docker run -d \
	--name postgres-db \
  	-e POSTGRES_PASSWORD=testing \
  	-e POSTGRES_DB=Doorbell \
  	-p 5432:5432 \
  	-v postgres_data:/var/lib/postgresql/data \
  	postgres
