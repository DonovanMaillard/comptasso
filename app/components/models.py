from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from .init_db import db
from sqlalchemy.dialects.postgresql import UUID

#############################
## TABLES DE DICTIONNAIRES ##
#############################

class dictBudgetTypes(db.Model):

    __tablename__ = "dict_budget_types"
    __table_args__ = {"schema": "comptasso"}
    id_type_budget = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)


class dictBudgetActionTypes(db.Model):

    __tablename__ = "dict_budget_action_types"
    __table_args__ = {"schema": "comptasso"}
    id_budget_action_types = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)


class dictPaymentMethods(db.Model):

    __tablename__ = "dict_payment_methods"
    __table_args__ = {"schema": "comptasso"}
    id_payment_method = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)


class dictOperationTypes(db.Model):

    __tablename__ = "dict_operation_types"
    __table_args__ = {"schema": "comptasso"}
    id_type_operation = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    operator = db.Column(db.String(1), nullable=True)


class dictCategories(db.Model):

    __tablename__ = "dict_categories"
    __table_args__ = {"schema": "comptasso"}
    id_category = db.Column(db.Integer, primary_key=True)
    cd_category = db.Column(db.Integer, nullable=True)
    label = db.Column(db.String(255), nullable=False)
    detail = db.Column(db.String(255), nullable=True)
    level = db.Column(db.Integer, nullable=True)
    cd_broader = db.Column(db.Integer, nullable=True)
    id_type_operation = db.Column(db.Integer, nullable=True)
    seizable = db.Column(db.Boolean, nullable=False)


#######################
## TABLES DE DONNEES ##
#######################

class tFunders(db.Model):

    __tablename__ = "t_funders"
    __table_args__ = {"schema": "comptasso"}
    id_funder = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), nullable=True)
    logo_url = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    zip_code = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Unicode, nullable=True)
    active = db.Column(db.Boolean, nullable=True)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__(self, name, code, logo_url, address, city, zip_code, comment, active):
        self.name = name
        self.code = code
        self.logo_url = logo_url
        self.address = address
        self.city = city
        self.zip_code = zip_code
        self.comment = comment
        self.active = active


class tBudgets(db.Model):

    __tablename__ = "t_budgets"
    __table_args__ = {"schema": "comptasso"}
    id_budget = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(255), nullable=True)
    id_funder = db.Column(db.Integer(), nullable=True)
    id_type_budget = db.Column(db.Integer(), nullable=True)
    date_max_expenditure = db.Column(db.Date(), nullable=True)
    date_return = db.Column(db.Date(), nullable=True)
    budget_amount = db.Column(db.Numeric(8,2), nullable=True)
    payroll_limit = db.Column(db.Numeric(8,2), nullable=True)
    indirect_charges = db.Column(db.Numeric(8,2), nullable=True)
    comment = db.Column(db.Unicode, nullable=True)
    allowed_fixed_cost = db.Column(db.Boolean, nullable=True)
    active = db.Column(db.Boolean, nullable=True)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__(self, name, reference, id_funder, id_type_budget, date_max_expenditure, date_return, budget_amount, payroll_limit, indirect_charges, comment, allowed_fixed_cost, active):
        self.name = name
        self.reference = reference
        self.id_funder = id_funder
        self.id_type_budget = id_type_budget
        self.date_max_expenditure = date_max_expenditure
        self.date_return = date_return
        self.budget_amount = budget_amount
        self.payroll_limit = payroll_limit
        self.indirect_charges = indirect_charges
        self.comment = comment
        self.allowed_fixed_cost = allowed_fixed_cost
        self.active = active


class tAccounts(db.Model):

    __tablename__ = "t_accounts"
    __table_args__ = {"schema": "comptasso"}
    id_account = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.BigInteger(), nullable=False)
    bank = db.Column(db.String(50), nullable=True)
    bank_url = db.Column(db.String(255), nullable=True)
    iban = db.Column(db.String(50), nullable=True)
    uploaded_file = db.Column(db.String(255), nullable=True)
    is_personnal = db.Column(db.Boolean, nullable=True)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__(self, name, account_number, bank, bank_url, iban, uploaded_file, is_personnal):
        self.name = name
        self.account_number = account_number
        self.bank = bank
        self.bank_url = bank_url
        self.iban = iban
        self.uploaded_file = uploaded_file
        self.is_personnal = is_personnal


class tOperations(db.Model):

    __tablename__ = "t_operations"
    __table_args__ = {"schema": "comptasso"}
    id_operation = db.Column(db.Integer, primary_key=True)
    id_grp_operation = db.Column(UUID(as_uuid=True), primary_key=False, nullable=True)
    name = db.Column(db.String(50), nullable=False)
    detail_operation = db.Column(db.Unicode, nullable=True)
    id_type_operation = db.Column(db.Integer(), nullable=True)
    operation_date = db.Column(db.Date(), nullable=True)
    effective_date = db.Column(db.Date(), nullable=True)
    amount = db.Column(db.Numeric(8,2), nullable=False)
    id_payment_method = db.Column(db.Integer(), nullable=True)
    id_account = db.Column(db.Integer(), nullable=False)
    id_budget = db.Column(db.Integer(), nullable=False)
    id_category = db.Column(db.Integer(), nullable=True)
    uploaded_file = db.Column(db.String(255), nullable=False)
    pointed = db.Column(db.Boolean, nullable=True)
    meta_id_digitiser = db.Column(db.Integer(), nullable=True)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__(self, id_grp_operation, name, detail_operation, id_type_operation, operation_date, effective_date, amount, id_payment_method, id_account, id_budget, id_category, uploaded_file, pointed, meta_id_digitiser):
        self.id_grp_operation = id_grp_operation
        self.name = name
        self.detail_operation = detail_operation
        self.id_type_operation = id_type_operation 
        self.operation_date = operation_date
        self.effective_date = effective_date
        self.amount = amount
        self.id_payment_method = id_payment_method
        self.id_account = id_account
        self.id_budget = id_budget
        self.id_category = id_category
        self.uploaded_file = uploaded_file
        self.pointed = pointed
        self.meta_id_digitiser = meta_id_digitiser


class tMembers(db.Model):

    __tablename__ = "t_members"
    __table_args__ = {"schema": "comptasso"}
    id_member = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(50), nullable=False)
    member_role = db.Column(db.String(255), nullable=False)
    is_employed = db.Column(db.Boolean, nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__(self, member_name, member_role, is_employed, active):
        self.member_name = member_name
        self.member_role = member_role
        self.is_employed = is_employed 
        self.active = active


class tUsers(UserMixin, db.Model):

    __tablename__ = "t_users"
    __table_args__ = {"schema": "comptasso"}
    id_user = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    firstname = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    login = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__(self, name, firstname, email, login, password, is_active):
        self.name = name
        self.firstname = firstname
        self.email = email 
        self.login = login
        self.password = password
        self.is_active = is_active

    def get_id(self):
           return (self.id_user)


class loginHistory(db.Model):

    __tablename__ = "login_history"
    __table_args__ = {"schema": "comptasso"}
    id_session = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, nullable=False)
    login_time = db.Column(db.DateTime(), nullable=False)
    
    def __init__(self, id_user, login_time):
        self.id_user = id_user
        self.login_time = login_time 

        
###############################
## TABLES DE CORRESPONDANCES ##
###############################

class corActionBudget(db.Model):

    __tablename__ = "cor_action_budget"
    __table_args__ = {"schema": "comptasso"}
    id_action_budget = db.Column(db.Integer, primary_key=True)
    id_budget_action_types = db.Column(db.Integer, nullable=False)
    id_budget = db.Column(db.Integer, nullable=False)
    date_action = db.Column(db.Date(), nullable=False)
    description_action =  db.Column(db.String(255), nullable=True)
    uploaded_file =  db.Column(db.String(255), nullable=True)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__ (self, id_budget_action_types, id_budget, date_action, description_action, uploaded_file):
        self.id_budget_action_types = id_budget_action_types
        self.id_budget = id_budget
        self.date_action = date_action
        self.description_action = description_action
        self.uploaded_file = uploaded_file


class corMemberPayroll(db.Model):

    __tablename__ = "cor_member_payroll"
    __table_args__ = {"schema": "comptasso"}
    id_payroll = db.Column(db.Integer, primary_key=True)
    id_member = db.Column(db.Integer, nullable=False)
    date_min_period = db.Column(db.Date(), nullable=False)
    date_max_period = db.Column(db.Date(), nullable=False)
    member_net_gain = db.Column(db.Numeric(8,2), nullable=False)
    member_charge_amount = db.Column(db.Numeric(8,2), nullable=False)
    employer_charge_amount = db.Column(db.Numeric(8,2), nullable=False)
    real_worked_days = db.Column(db.Numeric(8,2), nullable=False)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__ (self, id_member, date_min_period, date_max_period, member_net_gain, member_charge_amount, employer_charge_amount, real_worked_days):
        self.id_member = id_member
        self.date_min_period = date_min_period
        self.date_max_period = date_max_period
        self.member_net_gain = member_net_gain
        self.member_charge_amount = member_charge_amount
        self.employer_charge_amount = employer_charge_amount
        self.real_worked_days = real_worked_days


class corPayrollBudget(db.Model):

    __tablename__ = "cor_payroll_budget"
    __table_args__ = {"schema": "comptasso"}
    id_payroll_budget = db.Column(db.Integer, primary_key=True)
    id_budget = db.Column(db.Integer, nullable=False)
    id_member = db.Column(db.Integer, nullable=False)
    date_min_period = db.Column(db.Date(), nullable=False)
    date_max_period = db.Column(db.Date(), nullable=False)
    nb_days_allocated = db.Column(db.Numeric(8,2), nullable=False)
    fixed_cost = db.Column(db.Numeric(8,2), nullable=False)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)

    def __init__ (self, id_budget, id_member, date_min_period, date_max_period, nb_days_allocated, fixed_cost):
        self.id_budget = id_budget
        self.id_member = id_member
        self.date_min_period = date_min_period
        self.date_max_period = date_max_period
        self.nb_days_allocated = nb_days_allocated
        self.fixed_cost = fixed_cost


##########
## VUES ##
##########

class vBudgets(db.Model):

    __tablename__ = "v_budgets"
    __table_args__ = {"schema": "comptasso"}
    id_budget = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(255), nullable=True)
    id_funder = db.Column(db.Integer, nullable=True)
    funder = db.Column(db.String(50), nullable=True)
    type_budget = db.Column(db.String(50), nullable=True)
    date_max_expenditure = db.Column(db.Date(), nullable=True)
    date_return = db.Column(db.Date(), nullable=True)
    budget_amount = db.Column(db.Numeric(8,2), nullable=True)
    payroll_limit = db.Column(db.Numeric(8,2), nullable=True)
    indirect_charges = db.Column(db.Numeric(8,2), nullable=True)
    indirect_charges_amount = db.Column(db.Numeric(8,2), nullable=True)
    comment = db.Column(db.Unicode, nullable=True)
    active = db.Column(db.Boolean, nullable=True)
    received_amount = db.Column(db.Numeric(8,2), nullable=True)
    percent_received = db.Column(db.Numeric(8,2), nullable=True)
    spent_amount = db.Column(db.Numeric(8,2), nullable=True)
    percent_spent = db.Column(db.Numeric(8,2), nullable=True)
    committed_amount = db.Column(db.Numeric(8,2), nullable=True)
    percent_committed = db.Column(db.Numeric(8,2), nullable=True)
    last_operation = db.Column(db.Date(), nullable=True)
    last_action_date = db.Column(db.Date(), nullable=True)


class vAccounts(db.Model):

    __tablename__ = "v_accounts"
    __table_args__ = {"schema": "comptasso"}
    id_account = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.Integer(), nullable=True)
    bank = db.Column(db.String(50), nullable=False)
    bank_url = db.Column(db.String(255), nullable=False)
    iban = db.Column(db.String(50), nullable=False)
    uploaded_file = db.Column(db.String(50), nullable=False)
    is_personnal = db.Column(db.Boolean, nullable=True)
    meta_create_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)
    account_balance = db.Column(db.Numeric(8,2), nullable=True)
    account_commitments = db.Column(db.Numeric(8,2), nullable=True)
    last_operation = db.Column(db.Date(), nullable=True)


class vActions(db.Model):

    __tablename__ = "v_actions"
    __table_args__ = {"schema": "comptasso"}
    id_action_budget = db.Column(db.Integer, primary_key=True)
    id_budget = db.Column(db.Integer, nullable=False)
    date_action = db.Column(db.Date, nullable=False)
    type_action = db.Column(db.String(50), nullable=False)
    description_action = db.Column(db.String(255), nullable=True)
    uploaded_file = db.Column(db.String(255), nullable=True)


class vOperations(db.Model):

    __tablename__ = "v_operations"
    __table_args__ = {"schema": "comptasso"}
    id_operation = db.Column(db.Integer, primary_key=True)
    id_grp_operation = db.Column(UUID(as_uuid=True), nullable=False)
    name_operation = db.Column(db.String(50), nullable=False)
    detail_operation = db.Column(db.Unicode, nullable=True)
    id_type_operation = db.Column(db.Integer, nullable=False)
    type_operation = db.Column(db.String(50), nullable=False)
    operation_date = db.Column(db.Date, nullable=True)
    effective_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(8,2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    id_account = db.Column(db.Integer, nullable=False)
    account_name = db.Column(db.String(50), nullable=False)
    personnal_account = db.Column(db.Boolean, nullable=True)
    id_budget = db.Column(db.Integer, nullable=True)
    budget_name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    parent_category = db.Column(db.String(50), nullable=False)
    uploaded_file = db.Column(db.String(255), nullable=True)
    pointed = db.Column(db.Boolean, nullable=True)
    meta_crate_date = db.Column(db.DateTime(), nullable=True)
    meta_update_date = db.Column(db.DateTime(), nullable=True)


class vPayrolls(db.Model):

    __tablename__ = "v_payrolls"
    __table_args__ = {"schema": "comptasso"}

    id_payroll = db.Column(db.Integer, primary_key=True)
    id_member = db.Column(db.Integer, nullable=False)
    member_name = db.Column(db.String(50), nullable=False)
    date_min_period = db.Column(db.Date(), nullable=False)
    date_max_period = db.Column(db.Date(), nullable=False)
    member_net_gain = db.Column(db.Numeric(8,2), nullable=False)
    member_charge_amount = db.Column(db.Numeric(8,2), nullable=False)
    employer_charge_amount = db.Column(db.Numeric(8,2), nullable=False)
    total_amount = db.Column(db.Numeric(8,2), nullable=False)
    real_worked_days = db.Column(db.Numeric(8,2), nullable=False)


class vPayrollDetails(db.Model):

    __tablename__ = "v_payroll_details"
    __table_args__ = {"schema": "comptasso"}
    id_payroll_budget = db.Column(db.Integer, primary_key=True)
    id_budget = db.Column(db.Integer, nullable=False)
    id_member = db.Column(db.Integer, nullable=False)
    member_role = db.Column(db.Unicode, nullable=False)
    date_min_period = db.Column(db.Date, nullable=False)
    date_max_period = db.Column(db.Date, nullable=False)
    total_worked_days_on_period = db.Column(db.Numeric(8,2), nullable=True)
    total_brut_cost_on_period = db.Column(db.Numeric(8,2), nullable=True)
    total_employer_charges_on_period = db.Column(db.Numeric(8,2), nullable=True)
    total_payroll_on_period = db.Column(db.Numeric(8,2), nullable=True)
    daily_payroll_on_period = db.Column(db.Numeric(8,2), nullable=True)
    nb_days_allocated = db.Column(db.Numeric(8,2), nullable=False)
    fixed_cost = db.Column(db.Numeric(8,2), nullable=True)
    applied_payroll = db.Column(db.Numeric(8,2), nullable=False)
