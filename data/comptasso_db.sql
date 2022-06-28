DROP SCHEMA IF EXISTS comptasso;
CREATE SCHEMA comptasso;

-- TABLES DE DICTIONNAIRES 

CREATE TABLE comptasso.dict_budget_types (
	id_type_budget serial PRIMARY KEY,
	label varchar(50),
	description varchar(255)
); --OK, alimenté

CREATE TABLE comptasso.dict_budget_action_types (
	id_budget_action_types serial PRIMARY KEY,
	label varchar(50),
	description varchar(255)
); --OK, alimenté

-- PAYMENT_METHODS
CREATE TABLE comptasso.dict_payment_methods (
	id_payment_method serial PRIMARY KEY,
	label varchar(50) NOT NULL,
	description varchar(255)
); -- OK alimenté

-- OPERATION_TYPES
CREATE TABLE comptasso.dict_operation_types (
	id_type_operation serial PRIMARY KEY,
	label varchar(50),
	description varchar(255),
	operator varchar(1)
); --OK alimenté

CREATE TABLE comptasso.dict_categories (
	id_category serial PRIMARY KEY,
	cd_category integer,
	label varchar(255) NOT NULL,
	detail varchar(255),
	level integer,
	cd_broader integer,
	id_type_operation integer,
	seizable boolean
);

CREATE TABLE comptasso.dict_kilometric_scale (
	id_kilometric_scale serial PRIMARY KEY,
	start_date date NOT NULL,
	end_date date NOT NULL,
	fiscal_power integer NOT NULL,
	kilometric_scale numeric(8,2) NOT NULL,
	active boolean
);

-- 
-- TABLES DE DONNEES DYNAMIQUES

CREATE TABLE comptasso.t_funders (
	id_funder serial PRIMARY KEY,
	name varchar(50) NOT NULL,
	code varchar(10),
	logo_url varchar(255),
	address varchar(255),
	city varchar(255),
	zip_code integer,
	comment TEXT,
	active boolean,
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE 
); --OK

CREATE TABLE comptasso.t_members (
	id_member serial PRIMARY KEY,
	member_name varchar(50),
	member_role varchar(50),
	is_employed boolean,
	active boolean DEFAULT true,
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE 
);

CREATE TABLE comptasso.t_budgets (
	id_budget serial PRIMARY KEY,
	name varchar(50) NOT NULL,
	reference varchar(50),
	id_funder integer,
	id_type_budget integer,
	date_max_expenditure date, -- Date maximale d'éligibilité des dépenses
	date_return date, -- Date de rendu (bilans comptables, rapports et autres documents administratifs liés au budget)
	budget_amount numeric(8,2),
	payroll_limit numeric(8,2), -- Masse salariale maximale
	indirect_charges numeric(8,2), -- Charges indirectes(%)
	comment text,
	allowed_fixed_cost boolean,
	active boolean,
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE
); --OK

CREATE TABLE comptasso.t_accounts (
	id_account serial PRIMARY KEY,
	name varchar(50) NOT NULL,
	account_number bigint NOT NULL,
	bank varchar(50),
	bank_url varchar(255),
	iban varchar(50), 
	uploaded_file varchar(255),
	is_personnal boolean,
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE
);--OK 

CREATE TABLE comptasso.t_operations (
	id_operation serial PRIMARY KEY,
	id_grp_operation uuid,
	name varchar(50) NOT NULL,
	detail_operation varchar(255),
	id_type_operation integer,
	operation_date date,
	effective_date date,
	amount numeric(8,2) NOT NULL, -- Les débits sont stockés avec un nombre négatif, les crédits avec un nombre positif
	id_payment_method integer,
	id_account integer NOT NULL,
	id_budget integer,
	id_category integer NOT NULL,
	uploaded_file varchar(255),
	pointed boolean DEFAULT false,
	meta_id_digitiser integer,
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE
);

CREATE TABLE comptasso.t_users (
	id_user serial PRIMARY KEY,
	name varchar(100), 
	firstname varchar(100),
	email varchar(100),
	login varchar(50) NOT NULL,
	password varchar(255) NOT NULL,
	is_active boolean DEFAULT FALSE,
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE
);

CREATE TABLE comptasso.login_history (
	id_session serial PRIMARY KEY,
	id_user integer NOT NULL,
	login_time timestamp without time zone NOT NULL DEFAULT now()
);

--
-- CORRESPONDANCES
CREATE TABLE comptasso.cor_action_budget (
	id_action_budget serial PRIMARY KEY,
	id_budget_action_types integer NOT NULL,
	id_budget integer NOT NULL,
	date_action date NOT NULL,
	description_action varchar(255),
	uploaded_file varchar(255),
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE
);--OK


CREATE TABLE comptasso.cor_member_payroll (
	id_payroll serial PRIMARY KEY,
	id_member integer NOT NULL,
	date_min_period date NOT NULL,
	date_max_period date NOT NULL,
	member_net_gain numeric(8,2) NOT NULL,
	member_charge_amount numeric(8,2) NOT NULL,
	employer_charge_amount numeric(8,2) NOT NULL,
	real_worked_days numeric(8,2) NOT NULL,
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE
);

CREATE TABLE comptasso.cor_payroll_budget (
	id_payroll_budget serial PRIMARY KEY,
	id_budget integer NOT NULL,
	id_member integer NOT NULL,
	date_min_period date NOT NULL,
	date_max_period date NOT NULL,
	nb_days_allocated numeric(8,2) NOT NULL,
	fixed_cost numeric(8,2),
	meta_create_date timestamp WITHOUT time ZONE,
	meta_update_date timestamp WITHOUT time ZONE
);



--
-- FONCTIONS & FONCTIONS TRIGGERS
CREATE OR REPLACE FUNCTION comptasso.get_sum_movement(cur_id_budget integer, cur_operation_type text)
RETURNS numeric(8,2)
LANGUAGE plpgsql IMMUTABLE
    AS $$
-- Fonction permettant de connaitre la somme des mouvements d'un type donné pour un budget donné
  DECLARE 
   result numeric(8,2);
  BEGIN
   SELECT INTO result COALESCE(ABS(sum(amount)), 0) 
   FROM comptasso.t_operations op
   JOIN comptasso.dict_operation_types dot ON op.id_type_operation=dot.id_type_operation
   WHERE id_budget=cur_id_budget 
   AND dot.label=cur_operation_type;
   RETURN result;
  END;
$$;


CREATE OR REPLACE FUNCTION comptasso.get_account_balance(cur_id_account integer)
RETURNS numeric(8,2)
LANGUAGE plpgsql IMMUTABLE
    AS $$
-- Fonction permettant de connaitre le solde d'un compte donné
  DECLARE 
   balance numeric(8,2);
  BEGIN
   SELECT INTO balance sum(amount) 
   FROM comptasso.t_operations op
   JOIN comptasso.dict_operation_types dot ON op.id_type_operation=dot.id_type_operation
   WHERE id_account=cur_id_account 
   AND dot.label!='Engagement';
   RETURN balance;
  END;
$$;


CREATE OR REPLACE FUNCTION comptasso.get_account_commitment(cur_id_account integer)
RETURNS numeric(8,2)
LANGUAGE plpgsql IMMUTABLE
    AS $$
-- Fonction permettant de connaitre les engagements pour un compte donné
  DECLARE 
   balance numeric(8,2);
  BEGIN
   SELECT INTO balance sum(amount) 
   FROM comptasso.t_operations op
   JOIN comptasso.dict_operation_types dot ON op.id_type_operation=dot.id_type_operation
   WHERE id_account=cur_id_account 
   AND dot.label='Engagement';
   RETURN balance;
  END;
$$;


CREATE OR REPLACE FUNCTION comptasso.get_payroll_details(cur_id_member integer, cur_date_min_period date, cur_date_max_period date)
RETURNS table(total_brut_cost_on_period numeric(8,2), total_employer_charges_on_period numeric(8,2), total_payroll_on_period numeric(8,2), total_worked_days_on_period numeric(8,2))
LANGUAGE plpgsql IMMUTABLE
    AS $$
-- Fonction permettant de calculer - pour un employé donné sur une période donnée - la masse salariale réelle et le nombre de jours ouvrés réels appliqués
-- Cette fonction tient compte des mois complets intersectant la période recherchée. Par exemple, si je cherche la période du 23 janvier au 8 février, la
-- fonction retournera la rémunération nette, brute, et la masse salariale gloable ainsi que les jours ouvrés réels pour la période du 1er janvier au 28 février.
-- Utilisé pour la valorisation du temps salarié au réel sur la période d'actions d'une ligne budgétaire
  BEGIN
  	return query 
	SELECT 
		sum(cep.member_net_gain)+sum(cep.member_charge_amount) AS total_brut_cost_on_period,
		sum(cep.employer_charge_amount) AS total_employer_charges_on_period,
		sum(cep.member_net_gain)+sum(cep.member_charge_amount)+sum(cep.employer_charge_amount) AS total_payroll_on_period,
		sum(cep.real_worked_days) AS total_worked_days_on_period
	FROM comptasso.cor_member_payroll cep
	WHERE cep.id_member=cur_id_member
	AND cur_date_min_period <= cep.date_max_period
	AND cur_date_max_period >= cep.date_min_period;
  END;
$$;


-- Fonction trigger calculant les meta_create_date et meta_update_date
CREATE OR REPLACE FUNCTION public.fct_trg_meta_dates_change()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
        if(TG_OP = 'INSERT') THEN
                NEW.meta_create_date = NOW();
        ELSIF(TG_OP = 'UPDATE') THEN
                NEW.meta_update_date = NOW();
                if(NEW.meta_create_date IS NULL) THEN
                        NEW.meta_create_date = NOW();
                END IF;
        end IF;
        return NEW;
end;
$function$
;


-- Create triggers on tables with meta_date fields
CREATE TRIGGER tri_meta_dates_change_t_funders
BEFORE INSERT OR UPDATE ON comptasso.t_funders 
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_t_members 
BEFORE INSERT OR UPDATE ON comptasso.t_members
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_t_budgets 
BEFORE INSERT OR UPDATE ON comptasso.t_budgets
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_t_accounts 
BEFORE INSERT OR UPDATE ON comptasso.t_accounts 
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_t_operations 
BEFORE INSERT OR UPDATE ON comptasso.t_operations 
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_t_users 
BEFORE INSERT OR UPDATE ON comptasso.t_users 
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_cor_action_budget 
BEFORE INSERT OR UPDATE ON comptasso.cor_action_budget 
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_cor_member_payroll 
BEFORE INSERT OR UPDATE ON comptasso.cor_member_payroll 
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();

CREATE TRIGGER tri_meta_dates_change_cor_payroll_budget 
BEFORE INSERT OR UPDATE ON comptasso.cor_payroll_budget 
FOR EACH ROW EXECUTE PROCEDURE fct_trg_meta_dates_change();


--
-- VUES CALCULEES
CREATE VIEW comptasso.v_accounts AS (
	SELECT 
		ac.id_account, 
		ac.name AS name, 
		ac.account_number AS account_number,
		ac.bank AS bank,
		ac.bank_url AS bank_url,
		ac.iban AS iban, 
		ac.uploaded_file AS uploaded_file,
		ac.is_personnal AS is_personnal,
		ac.meta_create_date AS meta_create_date,
		ac.meta_update_date AS meta_update_date,
		comptasso.get_account_balance(ac.id_account) AS account_balance,
		comptasso.get_account_commitment(ac.id_account) AS account_commitments,
		max(op.effective_date) AS last_operation
	FROM comptasso.t_accounts ac
	LEFT JOIN comptasso.t_operations op ON op.id_account=ac.id_account
	GROUP BY ac.id_account, ac.name, ac.account_number, ac.bank, ac.iban, ac.uploaded_file, ac.meta_create_date, ac.meta_update_date
	ORDER BY name
); 


CREATE VIEW comptasso.v_budgets AS (
 SELECT b.id_budget,
    b.name,
    b.reference,
    f.id_funder AS id_funder,
    f.name AS funder,
    bt.label AS type_budget,
    COALESCE (b.date_max_expenditure::text, '-') AS date_max_expenditure,
    COALESCE (b.date_return::text, '-') AS date_return,
    COALESCE (b.budget_amount, 0)::numeric(8,2) AS budget_amount,
    COALESCE (b.payroll_limit, 0)::numeric(8,2) AS payroll_limit,
    COALESCE (b.indirect_charges, 0)::numeric(8,2) AS indirect_charges,
    COALESCE ((b.indirect_charges/100)*b.payroll_limit, 0)::numeric(8,2) AS indirect_charges_amount,
    b.comment,
    b.active,
    comptasso.get_sum_movement(b.id_budget, 'Recette') AS received_amount,
    ((comptasso.get_sum_movement(b.id_budget, 'Recette')/b.budget_amount)*100)::numeric(8,2) AS percent_received,
    comptasso.get_sum_movement(b.id_budget, 'Dépense') AS spent_amount,
    ((comptasso.get_sum_movement(b.id_budget, 'Dépense')/b.budget_amount)*100)::numeric(8,2) AS percent_spent,
    comptasso.get_sum_movement(b.id_budget, 'Engagement') AS committed_amount, 
    ((comptasso.get_sum_movement(b.id_budget, 'Engagement')/b.budget_amount)*100)::numeric(8,2) AS percent_committed,   
    b.budget_amount - (comptasso.get_sum_movement(b.id_budget, 'Dépense') + comptasso.get_sum_movement(b.id_budget, 'Engagement')) AS available_amount,
    COALESCE (max(op.effective_date)::TEXT,'-') AS last_operation,
    COALESCE (max(cab.date_action)::TEXT, '-') AS last_action_date
   FROM comptasso.t_budgets b
     LEFT JOIN comptasso.dict_budget_types bt ON b.id_type_budget = bt.id_type_budget
     LEFT JOIN comptasso.t_funders f ON f.id_funder = b.id_funder
     LEFT JOIN comptasso.t_operations op ON op.id_budget = b.id_budget
     LEFT JOIN comptasso.cor_action_budget cab ON cab.id_budget = b.id_budget
  GROUP BY b.id_budget, b.name, b.reference, f.id_funder, f.name, bt.label, b.date_max_expenditure, 
  b.date_return, b.budget_amount, b.payroll_limit, b.indirect_charges, b.comment, b.active, 
  received_amount, percent_received, spent_amount, percent_spent, committed_amount, percent_committed, available_amount
  )
  ORDER BY active, name
;


CREATE VIEW comptasso.v_actions AS (
	SELECT
		cab.id_action_budget,
		cab.id_budget, 
		cab.date_action AS date_action, 
		dbat.label AS type_action, 
		cab.description_action AS description_action,
		cab.uploaded_file AS uploaded_file
	FROM comptasso.cor_action_budget cab
	LEFT JOIN comptasso.dict_budget_action_types dbat ON dbat.id_budget_action_types=cab.id_budget_action_types
	ORDER BY cab.date_action
);


CREATE VIEW comptasso.v_operations AS (
	SELECT
		op.id_operation AS id_operation,
		op.id_grp_operation AS id_grp_operation,
		op.name AS name_operation,
		op.detail_operation AS detail_operation,
		dot.id_type_operation AS id_type_operation,
		dot.label AS type_operation,
		op.operation_date AS operation_date,
		op.effective_date AS effective_date,
		op.amount AS amount, -- Les débits sont stockés avec un nombre négatif, les crédits avec un nombre positif
		dpm.label AS payment_method,
		op.id_account AS id_account,
		ac.name AS account_name,
		ac.is_personnal AS personnal_account,
		op.id_budget AS id_budget,
		b.name AS budget_name,
		cat.cd_category||'. '||cat.label AS category,
		cat2.cd_category||'. ' ||cat2.label AS parent_category,
		op.uploaded_file AS uploaded_file,
		op.pointed AS pointed,
		op.meta_create_date AS meta_crate_date,
		op.meta_update_date AS meta_update_date
	FROM comptasso.t_operations op
	LEFT JOIN comptasso.dict_operation_types dot ON dot.id_type_operation=op.id_type_operation
	LEFT JOIN comptasso.dict_payment_methods dpm ON dpm.id_payment_method=op.id_payment_method
	LEFT JOIN comptasso.t_accounts ac ON ac.id_account=op.id_account
	LEFT JOIN comptasso.t_budgets b ON b.id_budget=op.id_budget
	LEFT JOIN comptasso.dict_categories cat ON cat.id_category=op.id_category
	LEFT JOIN comptasso.dict_categories cat2 ON cat.cd_broader=cat2.cd_category
	ORDER BY effective_date
);

CREATE VIEW comptasso.v_payrolls AS (
	SELECT
		cmp.id_payroll,
		cmp.id_member,
		m.member_name,
		cmp.date_min_period,
		cmp.date_max_period,
		cmp.member_net_gain,
		cmp.member_charge_amount,
		cmp.employer_charge_amount,
		cmp.member_net_gain+cmp.member_charge_amount+cmp.employer_charge_amount as total_amount, 
		cmp.real_worked_days
	FROM comptasso.cor_member_payroll cmp
	JOIN comptasso.t_members m ON cmp.id_member=m.id_member
	ORDER BY cmp.date_min_period
);

CREATE VIEW comptasso.v_payroll_details AS (
	SELECT 
		cpb.id_payroll_budget AS id_payroll_budget,
		b.id_budget AS id_budget,
		cpb.id_member AS id_member,
		m.member_name AS member_name,
		m.member_role AS member_role,
		min(cpb.date_min_period) AS date_min_period,
		max(cpb.date_max_period) AS date_max_period,
		(SELECT total_worked_days_on_period FROM comptasso.get_payroll_details(cpb.id_member, min(cpb.date_min_period), max(cpb.date_max_period))) AS total_worked_days_on_period,
		(SELECT total_brut_cost_on_period FROM comptasso.get_payroll_details(cpb.id_member, min(cpb.date_min_period), max(cpb.date_max_period))) AS total_brut_cost_on_period,
		(SELECT total_employer_charges_on_period FROM comptasso.get_payroll_details(cpb.id_member, min(cpb.date_min_period), max(cpb.date_max_period))) AS total_employer_charges_on_period,
		(SELECT total_payroll_on_period FROM comptasso.get_payroll_details(cpb.id_member, min(cpb.date_min_period), max(cpb.date_max_period))) AS total_payroll_on_period,
		(SELECT total_payroll_on_period/total_worked_days_on_period FROM comptasso.get_payroll_details(cpb.id_member, min(cpb.date_min_period), max(cpb.date_max_period))) AS daily_payroll_on_period,
		cpb.nb_days_allocated AS nb_days_allocated,
		cpb.fixed_cost AS fixed_cost,
		CASE 
			WHEN cpb.fixed_cost IS NULL 
			THEN cpb.nb_days_allocated*(SELECT total_payroll_on_period/total_worked_days_on_period FROM comptasso.get_payroll_details(cpb.id_member, min(cpb.date_min_period), max(cpb.date_max_period)))
			WHEN cpb.fixed_cost IS NOT NULL 
			THEN cpb.nb_days_allocated*cpb.fixed_cost
		END AS applied_payroll
	FROM comptasso.t_budgets b
	LEFT JOIN comptasso.cor_payroll_budget cpb ON cpb.id_budget = b.id_budget
	LEFT JOIN comptasso.t_members m ON m.id_member = cpb.id_member
	GROUP BY cpb.id_payroll_budget, b.id_budget, cpb.id_member, m.member_name, m.member_role, cpb.nb_days_allocated, cpb.fixed_cost
);



-----------------------------------
--- CONTRAINTES ET FOREIGN KEYS ---
-----------------------------------

ALTER TABLE comptasso.dict_categories 
ADD CONSTRAINT fk_dict_categories_id_type_operation FOREIGN KEY (id_type_operation) 
REFERENCES comptasso.dict_operation_types(id_type_operation) ON UPDATE CASCADE;

-- t_budgets
ALTER TABLE comptasso.t_budgets
ADD CONSTRAINT fk_t_budgets_id_funder FOREIGN KEY (id_funder) 
REFERENCES comptasso.t_funders(id_funder) ON UPDATE CASCADE;

ALTER TABLE comptasso.t_budgets
ADD CONSTRAINT fk_t_budgets_id_type_budget FOREIGN KEY (id_type_budget) 
REFERENCES comptasso.dict_budget_types(id_type_budget) ON UPDATE CASCADE;

-- t_operations
ALTER TABLE comptasso.t_operations
ADD CONSTRAINT fk_t_operations_id_account FOREIGN KEY (id_account) 
REFERENCES comptasso.t_accounts(id_account) ON UPDATE CASCADE;

ALTER TABLE comptasso.t_operations
ADD CONSTRAINT fk_t_operations_id_type_operation FOREIGN KEY (id_type_operation) 
REFERENCES comptasso.dict_operation_types(id_type_operation) ON UPDATE CASCADE;

ALTER TABLE comptasso.t_operations
ADD CONSTRAINT fk_t_operations_id_payment_method FOREIGN KEY (id_payment_method) 
REFERENCES comptasso.dict_payment_methods(id_payment_method) ON UPDATE CASCADE;

ALTER TABLE comptasso.t_operations
ADD CONSTRAINT fk_t_operations_id_budget FOREIGN KEY (id_budget) 
REFERENCES comptasso.t_budgets(id_budget) ON UPDATE CASCADE;

ALTER TABLE comptasso.t_operations
ADD CONSTRAINT fk_t_operations_id_category FOREIGN KEY (id_category) 
REFERENCES comptasso.dict_categories(id_category) ON UPDATE CASCADE;

-- cor_action_budget
ALTER TABLE comptasso.cor_action_budget
ADD CONSTRAINT fk_cor_action_budget_id_action_type FOREIGN KEY (id_budget_action_types) 
REFERENCES comptasso.dict_budget_action_types(id_budget_action_types) ON UPDATE CASCADE;

ALTER TABLE comptasso.cor_action_budget
ADD CONSTRAINT fk_cor_action_budget_id_budget FOREIGN KEY (id_budget) 
REFERENCES comptasso.t_budgets(id_budget) ON UPDATE CASCADE ON DELETE CASCADE;

-- cor_member_payroll
ALTER TABLE comptasso.cor_member_payroll
ADD CONSTRAINT fk_cor_member_payroll_id_member FOREIGN KEY (id_member) 
REFERENCES comptasso.t_members(id_member) ON UPDATE CASCADE;

-- cor_payroll_budget
ALTER TABLE comptasso.cor_payroll_budget
ADD CONSTRAINT fk_cor_payroll_budget_id_budget FOREIGN KEY (id_budget) 
REFERENCES comptasso.t_budgets(id_budget) ON UPDATE CASCADE;

ALTER TABLE comptasso.cor_payroll_budget
ADD CONSTRAINT fk_cor_payroll_budget_id_member FOREIGN KEY (id_member) 
REFERENCES comptasso.t_members(id_member) ON UPDATE CASCADE;

-- Avoid operations with amount of 0
ALTER TABLE comptasso.t_operations 
ADD CONSTRAINT t_operations_amount_is_not_zero CHECK (amount != 0);

-- Add unique constraint on login
ALTER TABLE comptasso.t_users
ADD CONSTRAINT unique_t_users_login UNIQUE (login);

-- Add foreign key on id_user
ALTER TABLE comptasso.login_history
ADD CONSTRAINT fk_login_history_id_user FOREIGN KEY (id_user) 
REFERENCES comptasso.t_users(id_user) ON UPDATE CASCADE;
