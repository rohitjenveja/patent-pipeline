CREATE TABLE run_status (id MEDIUMINT NOT NULL AUTO_INCREMENT, PRIMARY KEY(id), data_date DATETIME, run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
	                       run_status VARCHAR(200)); 