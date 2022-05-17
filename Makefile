dev: build
	echo "Starting dev server..."
	docker-compose -f docker-compose.dev.yml up;

build:
	echo "Building..."
	cd opservatory/client; npm run build;
	docker build -t opservatory .;
	echo "Done!"

back-dev:
	echo "Starting dev server..."
	docker-compose -f docker-compose.dev.yml up;

front-dev: 
	echo "Starting front-end dev server..."
	cd opservatory/client; npm run dev;

release: build
	docker tag opservatory $(tag)
	docker push $(tag)
