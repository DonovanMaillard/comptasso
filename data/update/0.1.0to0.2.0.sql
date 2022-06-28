-- FEATURE : authentication
-- Create users table
CREATE TABLE comptasso.t_users (
	id_user serial PRIMARY KEY,
	name varchar(100), 
	firstname varchar(100),
	email varchar(100),
	login varchar(50) NOT NULL,
	pass varchar(100) NOT NULL,
	active boolean DEFAULT FALSE
);

-- Create login_history table
CREATE TABLE comptasso.login_history (
	id_session serial PRIMARY KEY,
	id_user integer NOT NULL,
	login_time timestamp without time zone NOT NULL DEFAULT now()
);

-- Add foreign key on id_user
ALTER TABLE comptasso.login_history
ADD CONSTRAINT fk_login_history_id_user FOREIGN KEY (id_user) 
REFERENCES comptasso.t_users(id_user) ON UPDATE CASCADE;