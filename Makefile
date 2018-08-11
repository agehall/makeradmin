
build: .env
	docker-compose build

run: .env
	docker-compose up

init-npm:
	cd frontend && npm install 

init-pip:
	python3 -m pip install --upgrade -r requirements.txt

init: init-pip init-npm

init-db: .env
	python3 db_init.py

.env:
	python3 create_env.py

stop:
	docker-compose down

firstrun: .env build init-db
	echo -e "\e[31mRun 'make run' to start MakerAdmin\e[0m"

frontend-dev-server:
	mkdir -p frontend/node_modules
	docker-compose -f frontend/dev-server-compose.yaml rm -f
	docker volume rm makeradmin_node_modules
	docker-compose -f frontend/dev-server-compose.yaml up --build

.PHONY: build init-db
