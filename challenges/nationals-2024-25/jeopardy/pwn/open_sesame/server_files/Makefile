build:
	docker build --platform linux/amd64  -t build_challenge . -f Dockerfile.build
	docker run --rm -v $(PWD):/app build_challenge 

run: 
	docker-compose up --build

stop:
	docker-compose down