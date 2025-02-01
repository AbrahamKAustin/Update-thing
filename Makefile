# Load environment variables from .env file
include .env
export $(shell sed 's/=.*//' .env)

.PHONY: run_docker start_app stop_docker migrate_new migrate_upgrade migrate_all

# Run the PostgreSQL container with a volume
run_docker:
	@if [ ! "`docker ps -q -f name=company_registry_container`" ]; then \
		if [ "`docker ps -aq -f status=exited -f name=company_registry_container`" ]; then \
			echo "Starting existing Docker container..."; \
			docker start company_registry_container; \
		else \
			echo "Running new Docker container..."; \
			docker run --name company_registry_container -e POSTGRES_USER=$(POSTGRES_USER) -e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) -e POSTGRES_DB=$(POSTGRES_DB) -p 5432:5432 -v company_registry_data:/var/lib/postgresql/data -d postgres:13; \
		fi \
	else \
		echo "Docker container already running."; \
	fi

# Run the FastAPI application
start_app:
	uvicorn backend.registry_orm.main:app --reload

# Stop and remove the PostgreSQL container 

#DEACTIVATE THE VIRTUAL ENV!!!!!!
stop_docker:
	docker stop company_registry_container
	docker rm company_registry_container

# Create a new migration
migrate_new:
	cd backend/registry_orm && alembic revision --autogenerate -m "New migration"

# Apply database migrations
migrate_upgrade:
	cd backend/registry_orm && alembic upgrade head

# Create a new migration and apply it
migrate_all: migrate_new migrate_upgrade