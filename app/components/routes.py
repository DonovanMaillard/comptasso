from flask import Flask, render_template, request, flash, get_flashed_messages, redirect, url_for, make_response, stream_with_context
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.wrappers import Response
from io import StringIO
from datetime import datetime, timedelta
from flask_login import login_required, current_user, login_user, logout_user, LoginManager

#import logging
import os
import pdfkit
import csv
import uuid

from .init_db import db
from .models import *
from .forms import *


app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Load configuration
app.config.from_pyfile('../../config/config.py')
# To get one variable, tape app.config['MY_VARIABLE']


##################
# Authentication #
##################
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = u"L'authentification est obligatoire pour accéder à l'application. Veuillez vous connecter."
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id_user):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return tUsers.query.get(int(id_user))

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    form=formLogin(request.form)
    if request.method == 'POST' and form.validate():
        login = request.form.get('login')
        password = request.form.get('password')
        user = tUsers.query.filter_by(login=login).first()
        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password) or not user.is_active:
            flash('Mot de passe incorrect ou compte inactif. Si le problème persiste, veuillez contacter l\'administrateur')
            return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page
        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=True, duration=timedelta(minutes=1))
        track_login=loginHistory(
            user.id_user,
            datetime.now()
            )
        db.session.add(track_login)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

#SignUp
@app.route('/signup', methods=['GET','POST'])
def signup():
    form=formSignUp(request.form)
    if request.method == 'POST' and form.validate():
        if request.form.get('password') != request.form.get('password_confirm'):
            flash('Vous avez renseigné deux mots de passe différents, votre demande est invalide.', category="danger")
        if tUsers.query.filter_by(login=request.form['login']).first() is not None :
            flash('Un compte existe déjà avec cet identifiant.', category="danger")
        if request.form.get('password')==request.form.get('password_confirm') and not tUsers.query.filter_by(login=request.form['login']).first() :
            User = tUsers(
            request.form['name'],
            request.form['firstname'],
            request.form['email'],
            request.form['login'],
            generate_password_hash(request.form['password']),
            bool(False)
            )
            db.session.add(User)
            db.session.commit()
            flash('Votre demande d\'accès a bien été enregistrée. Un administrateur doit désormais activer votre compte.', category="success")
            return redirect(url_for('signup'))
    return render_template('signup.html', form=form)


# LogOut
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



#############
### UTILS ###
#############

#def allowed_file(filename):
#    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Todo : clean decimal inputs
def getDecimal(input):
    if input is None or input=='' :
        decimal=0.00
    else :
        decimal=abs(float(str(input).replace(',','.')))
    return decimal


def getChoiceOrNone(input):
    if input =='' or input is None:
        choice=None
    else:
        choice=input
    return choice


def getFileUrl(input):
    f = request.files.get(input)
    if f :
        filename = uuid.uuid4().hex[:10]+'_'+secure_filename(f.filename)
        f.save(app.config['BASE_DIR']+'app/static/uploads/'+filename)
        file_url='uploads/'+filename
    else :
        file_url=None
    return file_url


############
### MAIN ###
############

@app.route('/')
@login_required
def index():
    return render_template('home.html')

# Features
@app.route('/features')
@login_required
def features():
    return render_template('about/features.html')

# Tutorial
@app.route('/tutorial')
@login_required
def tutorial():
    return render_template('about/tutorial.html')

################
### ACCOUNTS ###
################
# List accounts
@app.route('/accounts/<type>')
@app.route('/accounts', defaults={'type': 'organism'})
@login_required
def accounts(type):
    if type == 'personnal' :
        Accounts = vAccounts.query.filter_by(is_personnal=True)
    else : 
        Accounts = vAccounts.query.filter_by(is_personnal=False)
    return render_template('accounts/accounts_list.html', Accounts = Accounts, Type = type)


# Detail account
@app.route('/accounts/detail/<id_account>', methods=['GET', 'POST'])
@login_required
def detailAccount(id_account):
    Account = vAccounts.query.get(id_account)
    page = request.args.get('page', 1, type=int)
    Operations = vOperations.query.filter(vOperations.id_account==id_account, vOperations.type_operation != 'Engagement').order_by(vOperations.effective_date.desc()).paginate(page=page, per_page=app.config['ROWS_PER_PAGE'])
    Commitments = vOperations.query.filter(vOperations.id_account==id_account, vOperations.type_operation == 'Engagement').order_by(vOperations.effective_date.desc()).all()
    return render_template('accounts/details_account.html', Account = Account, Operations = Operations, Commitments = Commitments )

# Add account
@app.route('/accounts/add/<type>', methods=['GET', 'POST'])
@app.route('/accounts/add', defaults={'type': 'organism'}, methods=['GET', 'POST'])
@login_required
def addAccount(type):
    form = formAccount(request.form)
    if type == 'personnal':
        is_personnal = True
    else : 
        is_personnal = False
    # Commit form
    if request.method == 'POST' and form.validate() :
        Account = tAccounts(
            request.form['name'],
            request.form['account_number'],
            request.form['bank'],
            request.form['bank_url'],
            request.form['iban'],
            getFileUrl('uploaded_file'),
            is_personnal
        )
        db.session.add(Account)
        db.session.commit()
        return redirect(url_for('accounts', type=type))
    return render_template('accounts/add_or_update_account.html', form=form, Account=None, active=None, Type=type)

# Edit account
@app.route('/accounts/edit/<id_account>', methods=['GET', 'POST'])
@login_required
def updateAccount(id_account):
  # pre-loaded form
    Account = tAccounts.query.get(id_account)
    form = formAccount(request.form, obj=Account)
    if request.method == 'POST' and form.validate():
        Account.name = request.form['name'], 
        Account.account_number = request.form['account_number'],
        Account.bank = request.form['bank'],
        Account.bank_url = request.form['bank_url'],
        Account.iban = request.form['iban'],
        if not request.form.get('keep_file'):
            Account.uploaded_file = getFileUrl('uploaded_file')
        db.session.commit()
        return redirect(url_for('accounts'))
    return render_template('accounts/add_or_update_account.html', form=form, Account=Account)

# Delete account
@app.route('/accounts/delete/<id_account>', methods=['GET', 'POST'])
@login_required
def deleteAccount(id_account):
    current_account=tAccounts.query.get(id_account)
    db.session.delete(current_account)
    db.session.commit()
    return redirect(url_for('accounts'))




###############
### BUDGETS ###
###############
#List budgets
@app.route('/budgets')
@login_required
def budgets():
    return render_template('budgets/budgets_list.html', Budgets = vBudgets.query.all())

# Details budget & list actions
@app.route('/budgets/detail/<id_budget>', methods=['GET', 'POST'])
@login_required
def detailBudget(id_budget):
    Budget = vBudgets.query.get(id_budget)
    Actions = vActions.query.filter_by(id_budget=id_budget)
    page = request.args.get('page', 1, type=int)
    Operations = vOperations.query.filter(vOperations.id_budget==id_budget, vOperations.type_operation != 'Engagement').order_by(vOperations.effective_date.desc()).paginate(page=page, per_page=app.config['ROWS_PER_PAGE'])
    Commitments = vOperations.query.filter(vOperations.id_budget==id_budget, vOperations.type_operation == 'Engagement').order_by(vOperations.effective_date.desc()).all()
    return render_template('budgets/details_budget.html', Budget = Budget, Actions = Actions, Operations = Operations, Commitments = Commitments)

# Add budget
@app.route('/budgets/add', methods=['GET', 'POST'])
@login_required
def addBudget():
    form = formBudget(request.form)
    print(form)
    # Funders
    activeFunders = tFunders.query.filter_by(active=True)
    form.id_funder.choices = [('', '-- Sélectionnez un financeur --')] + [(activeFunder.id_funder, activeFunder.name) for activeFunder in activeFunders]
    # Type budget
    TypesBudget = dictBudgetTypes.query.all()
    form.id_type_budget.choices = [('', '-- Sélectionnez un type --')] + [(TypeBudget.id_type_budget, TypeBudget.label) for TypeBudget in TypesBudget]
    if request.method == 'POST' and form.validate() :
        Budget = tBudgets(
            request.form['name'], 
            request.form['reference'], 
            getChoiceOrNone(request.form['id_funder']), 
            getChoiceOrNone(request.form['id_type_budget']), 
            request.form['date_max_expenditure'], 
            request.form['date_return'], 
            getDecimal(request.form['budget_amount']), 
            getDecimal(request.form['payroll_limit']), 
            getDecimal(request.form['indirect_charges']), 
            request.form['comment'], 
            bool(request.form.get('allowed_fixed_cost')),
            bool(request.form.get('active'))
        )
        db.session.add(Budget)
        db.session.commit()
        return redirect('/budgets')
    return render_template('budgets/add_or_update_budget.html', form=form, activeFunders=activeFunders, TypesBudget=TypesBudget, Budget=None, active=None, allowed=None)

# Edit budget
@app.route('/budgets/edit/<id_budget>', methods=['GET', 'POST'])
@login_required
def updateBudget(id_budget):
    # pre-loaded form
    Budget = tBudgets.query.get(id_budget)
    form = formBudget(request.form, obj=Budget)
    # Funders
    activeFunders = tFunders.query.filter_by(active=True)
    form.id_funder.choices = [('', '-- Sélectionnez un financeur --')] + [(activeFunder.id_funder, activeFunder.name) for activeFunder in activeFunders]
    form.id_funder.default = Budget.id_funder
    # Type budget
    TypesBudget = dictBudgetTypes.query.all()
    form.id_type_budget.choices = [('', '-- Sélectionnez un type --')] + [(TypeBudget.id_type_budget, TypeBudget.label) for TypeBudget in TypesBudget]
    form.id_type_budget.default = Budget.id_type_budget
    if request.method == 'POST' and form.validate():
        Budget.name = request.form['name'], 
        Budget.reference = request.form['reference'], 
        Budget.id_funder = getChoiceOrNone(request.form['id_funder']), 
        Budget.id_type_budget = getChoiceOrNone(request.form['id_type_budget']), 
        Budget.date_max_expenditure = request.form['date_max_expenditure'], 
        Budget.date_return = request.form['date_return'], 
        Budget.budget_amount = getDecimal(request.form['budget_amount']), 
        Budget.payroll_limit = getDecimal(request.form['payroll_limit']), 
        Budget.indirect_charges = getDecimal(request.form['indirect_charges']), 
        Budget.comment = request.form['comment'], 
        Budget.allowed_fixed_cost = bool(request.form.get('allowed_fixed_cost'))
        Budget.active = bool(request.form.get('active'))
        db.session.commit()
        return redirect('/budgets')
    return render_template('budgets/add_or_update_budget.html', form=form, Budget=Budget, active=Budget.active, allowed=Budget.allowed_fixed_cost)

# Delete budget
@app.route('/budgets/delete/<id_budget>', methods=['GET', 'POST'])
@login_required
def deleteBudget(id_budget):
    current_budget=tBudgets.query.get(id_budget)
    db.session.delete(current_budget)
    db.session.commit()
    return redirect('/budgets')


######################
### Budget actions ###
######################
# Add action
@app.route('/budgets/detail/<id_budget>/addAction', methods=['GET', 'POST'])
@login_required
def addAction(id_budget):
    form = formAction(request.form)
    Budget = tBudgets.query.get(id_budget)
    # Type Action
    TypesAction = dictBudgetActionTypes.query.all()
    form.id_budget_action_types.choices = [(TypeAction.id_budget_action_types, TypeAction.label) for TypeAction in TypesAction]
    # Charger le formulaire
    if request.method == 'POST' and form.validate() :
        Action = corActionBudget(
            getChoiceOrNone(request.form['id_budget_action_types']),
            Budget.id_budget, 
            request.form['date_action'],
            request.form['description_action'],
            getFileUrl('uploaded_file')
            )
        db.session.add(Action)
        db.session.commit()
        return redirect(url_for('detailBudget', id_budget=id_budget))
    return render_template('budgets/add_or_update_action.html', form=form, Budget=Budget, Action=None)


# Edit action
@app.route('/budgets/detail/<id_budget>/editAction/<id_action_budget>', methods=['GET', 'POST'])
@login_required
def updateAction(id_budget, id_action_budget):
    # pre-loaded form
    Action = corActionBudget.query.get(id_action_budget)
    form = formAction(request.form, obj=Action)
    # Type Action
    TypesAction = dictBudgetActionTypes.query.all()
    form.id_budget_action_types.choices = [(TypeAction.id_budget_action_types, TypeAction.label) for TypeAction in TypesAction]
    form.id_budget_action_types.default = Action.id_budget_action_types
    # Budget
    Budget = tBudgets.query.get(id_budget)
    # Charger le formulaire
    if request.method == 'POST' and form.validate():
        Action.id_budget_action_types = getChoiceOrNone(request.form['id_budget_action_types'])
        Action.id_budget = Budget.id_budget
        Action.date_action = request.form['date_action']
        Action.description_action = request.form['description_action']
        if not request.form.get('keep_file'):
            Action.uploaded_file = getFileUrl('uploaded_file')
        db.session.commit()
        return redirect(url_for('detailBudget', id_budget=id_budget))
    return render_template('budgets/add_or_update_action.html', form=form, Budget=Budget, Action=Action)


# Delete action
@app.route('/budgets/detail/<id_budget>/deleteAction/<id_action_budget>', methods=['GET', 'POST'])
@login_required
def deleteAction(id_budget, id_action_budget):
    current_action=corActionBudget.query.get(id_action_budget)
    db.session.delete(current_action)
    db.session.commit()
    return redirect(url_for('detailBudget', id_budget=id_budget))




##################
### OPERATIONS ###
##################

#####################
# Toutes opérations #
#####################

# Liste
@app.route('/operations', methods=['GET', 'POST'])
@login_required
def operations():
    # All operations
    Operations = vOperations.query.filter(vOperations.type_operation != 'Engagement').order_by(vOperations.effective_date.desc())
    # Results pagination
    page = request.args.get('page', 1, type=int)
    Operations = Operations.paginate(page=page, per_page=app.config['ROWS_PER_PAGE'])
    return render_template('operations/operations_list.html', Operations=Operations, type=None)

# Export CSV
@app.route('/operations/export_csv')
@login_required
def operationsCSV():
    @stream_with_context
    def generate():
        data = StringIO()
        w = csv.writer(data)

        # write header
        header=['Libelle','Detail','Type','Date_operation','Date_effet','Montant','Moyen_de_paiement','Compte','Budget','Categorie_fiscale','Categorie_parente','Date_creation','Derniere_modification']
        w.writerow(header)
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # write each item
        Operations = vOperations.query.filter(vOperations.type_operation != 'Engagement').order_by(vOperations.effective_date.desc()).all()
        for operation in Operations:
            print(operation)
            w.writerow((
                operation.id_grp_operation,
                operation.name_operation,
                operation.detail_operation,
                operation.type_operation,
                operation.operation_date,  
                operation.effective_date,  
                operation.amount,
                operation.payment_method,
                operation.account_name,
                operation.budget_name,
                operation.category,
                operation.parent_category,
                operation.meta_crate_date,
                operation.meta_update_date
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
        
    # stream the response as the data is generated
    response = Response(generate(), mimetype='text/csv')
    # add a filename
    response.headers.set("Content-Disposition", "attachment", filename=datetime.now().strftime("%Y%m%d_%H-%M-%S")+"_export_operations.csv")
    return response

# Suppression d'une opération ou de plusieurs opérations appariées
@app.route('/operations/<id_operation>/delete', methods=['GET', 'POST'])
@login_required
def deleteMovement(id_operation): 
    operation=tOperations.query.get(id_operation)
    db.session.delete(operation)
    db.session.commit()
    return redirect(url_for('operations'))



#######################
# Dépenses & Recettes #
#######################
# Ajout
@app.route('/operations/<type_operation>/add', methods=['GET', 'POST'])
@login_required
def addMovement(type_operation): #movement = Dépense + Recette
    #Get choices and form
    id_type_operation = dictOperationTypes.query.filter_by(label = type_operation).one().id_type_operation
    form = formMovement(request.form)
    # Get accounts
    Accounts = tAccounts.query.filter_by(is_personnal=False)
    # Form Choices
    # accounts
    form.id_account.choices = [('', '-- Sélectionnez un compte --')] + [(Account.id_account, Account.name) for Account in Accounts]
    # Budget
    activeBudgets = tBudgets.query.filter_by(active=True)
    form.id_budget.choices = [('', '-- Sélectionnez un budget --')] + [(activeBudget.id_budget, activeBudget.name) for activeBudget in activeBudgets]
    # Category
    Categories = dictCategories.query.filter(dictCategories.id_type_operation == id_type_operation, dictCategories.seizable == True).all()
    form.id_category.choices = [('', '-- Sélectionnez une catégorie --')] + [(category.id_category, str(category.cd_category)+" - "+category.label) for category in Categories]
    # Payment method
    PaymentMethods = dictPaymentMethods.query.all() # TODO filtrer avec la cor.
    form.id_payment_method.choices = [('', '-- Sélectionnez un moyen de paiement --')] + [(PaymentMethod.id_payment_method, PaymentMethod.label) for PaymentMethod in PaymentMethods]
    # allow null operation_date
    if request.form.get('operation_date') == '' and request.method == 'POST' and form.validate()  :
        operation_date = None
    else :
        operation_date = request.form.get('operation_date')
    # Get cleaned amound
    if type_operation == 'Dépense' and request.method == 'POST' and form.validate()  :
        amount = -getDecimal(request.form.get('amount'))
    else :
        amount = getDecimal(request.form.get('amount'))
    # Commit form
    if request.method == 'POST' and form.validate() :
        Operation = tOperations(
            None, #id_grp_operation
            request.form['name'],
            request.form['detail_operation'],
            id_type_operation,
            # allow None operation date
            operation_date,
            request.form['effective_date'],
            amount,
            getChoiceOrNone(request.form['id_payment_method']),
            getChoiceOrNone(request.form['id_account']),
            getChoiceOrNone(request.form['id_budget']),
            getChoiceOrNone(request.form['id_category']),
            getFileUrl('uploaded_file'),
            bool('false'),
            current_user.id_user
        )
        db.session.add(Operation)
        db.session.commit()
        return redirect(url_for('operations'))
    # Return form
    return render_template('operations/add_or_update_movement.html', form=form, Operation=None, type_operation=type_operation)


# Modification
@app.route('/operations/edit/<id_operation>', methods=['GET', 'POST'])
@login_required
def updateMovement(id_operation): #movement = Dépense + Recette
    # Pre-load form data
    # pre-loaded form
    Operation = tOperations.query.get(id_operation)
    type_operation = dictOperationTypes.query.filter_by(id_type_operation = Operation.id_type_operation).one().label
    #Get choices and form
    form = formMovement(request.form, obj=Operation)
    # Get accounts
    Accounts = tAccounts.query.filter_by(is_personnal=False)
    # Form Choices
    # accounts
    form.id_account.choices = [('', '-- Sélectionnez un compte --')] + [(Account.id_account, Account.name) for Account in Accounts]
    form.id_account.default=Operation.id_account
    # Budget
    activeBudgets = tBudgets.query.filter_by(active=True)
    form.id_budget.choices = [('', '-- Sélectionnez un budget --')] + [(activeBudget.id_budget, activeBudget.name) for activeBudget in activeBudgets]
    form.id_budget.default=Operation.id_budget
    # Category
    Categories = dictCategories.query.filter(dictCategories.id_type_operation == Operation.id_type_operation, dictCategories.seizable == True).all()
    form.id_category.choices = [('', '-- Sélectionnez une catégorie --')] + [(category.id_category, str(category.cd_category)+" - "+category.label) for category in Categories]
    form.id_category.default=Operation.id_category
    # Payment method
    PaymentMethods = dictPaymentMethods.query.all() # TODO filtrer avec la cor.
    form.id_payment_method.choices = [('', '-- Sélectionnez un moyen de paiement --')] + [(PaymentMethod.id_payment_method, PaymentMethod.label) for PaymentMethod in PaymentMethods]
    form.id_payment_method.default=Operation.id_payment_method
    # allow null operation_date
    if request.form.get('operation_date') == '' and request.method == 'POST' and form.validate()  :
        operation_date = None
    else :
        operation_date = request.form.get('operation_date')
    # Get cleaned amound
    if type_operation == 'Dépense' and request.method == 'POST' and form.validate()  :
        amount = -getDecimal(request.form.get('amount'))
    else :
        amount = getDecimal(request.form.get('amount'))
    # Update
    if request.method == 'POST' and form.validate():
        # let None as id_grp_operations
        Operation.name = request.form['name'],
        Operation.detail_operation = request.form['detail_operation'],
        # - let id_type_operation unchanged
        Operation.operation_date = operation_date
        Operation.effective_date = request.form['effective_date']
        Operation.amount = amount
        Operation.id_payment_method = getChoiceOrNone(request.form['id_payment_method'])
        Operation.id_account = getChoiceOrNone(request.form['id_account'])
        Operation.id_budget = getChoiceOrNone(request.form['id_budget'])
        Operation.id_category = getChoiceOrNone(request.form['id_category'])
        if not request.form.get('keep_file'):
            Operation.uploaded_file = getFileUrl('uploaded_file')
        Operation.meta_id_digitiser = current_user.id_user
        db.session.commit()
        return redirect(url_for('operations'))
    # Return form
    return render_template('operations/add_or_update_movement.html', form=form, Operation=Operation, type_operation=type_operation)


#######################
# Transferts internes #
#######################
# Add transfer
@app.route('/operations/transfer/<type_transfer>/add', methods=['GET', 'POST'])
@login_required
def addTransfer(type_transfer):
    #Get choices and form
    form = formTransfer(request.form)
    # Account
    FromAccounts = tAccounts.query.filter_by(is_personnal=False)
    if type_transfer == 'Internal' :
        ToAccounts = tAccounts.query.filter_by(is_personnal=False)
        id_type_operation = dictOperationTypes.query.filter_by(label = 'Transaction interne').one().id_type_operation
        id_category = dictCategories.query.filter_by(cd_category=100).one().id_category
    else :#refund
        ToAccounts = tAccounts.query.filter_by(is_personnal=True)
        id_type_operation = dictOperationTypes.query.filter_by(label = 'Remboursement de frais').one().id_type_operation
        id_category = dictCategories.query.filter_by(cd_category=110).one().id_category
    form.from_id_account.choices = [('', '-- Sélectionnez un compte débiteur --')] + [(FromAccount.id_account, FromAccount.name) for FromAccount in FromAccounts]
    form.to_id_account.choices = [('', '-- Sélectionnez un compte créditeur --')] + [(ToAccount.id_account, ToAccount.name) for ToAccount in ToAccounts]
    # Payment method
    PaymentMethods = dictPaymentMethods.query.all()
    form.id_payment_method.choices = [('', '-- Sélectionnez un moyen de paiement --')] + [(PaymentMethod.id_payment_method, PaymentMethod.label) for PaymentMethod in PaymentMethods]
    if request.method == 'POST' and form.validate() :
        id_grp_operation = uuid.uuid4() #id_grp_operation
        debit = tOperations(
            id_grp_operation,
            request.form['name'],
            request.form['detail_transfer'],
            id_type_operation,
            None,
            request.form['effective_date'],
            -getDecimal(request.form.get('amount')),
            getChoiceOrNone(request.form['id_payment_method']),
            request.form['from_id_account'],
            None, # budget id
            id_category,
            None,
            bool('false'),
            current_user.id_user
        )
        credit = tOperations(
            id_grp_operation,
            request.form['name'],
            request.form['detail_transfer'],
            id_type_operation,
            None,
            request.form['effective_date'],
            getDecimal(request.form.get('amount')),
            getChoiceOrNone(request.form['id_payment_method']),
            request.form['to_id_account'],
            None, #budget_id
            id_category,
            None,
            bool('false'),
            current_user.id_user
        )
        db.session.add(debit)
        db.session.add(credit)
        db.session.commit()
        return redirect(url_for('operations'))
    # return form
    return render_template('operations/add_or_update_transfer.html', form=form, Transfert=None, Type=type_transfer)

# Update transfert
@app.route('/operations/transfer/edit/<id_grp_operation>', methods=['GET', 'POST'])
@login_required
def updateTransfer(id_grp_operation):
    #Get updated objects
    credit= tOperations.query.filter_by(id_grp_operation=id_grp_operation).filter(tOperations.amount>0).first()
    debit= tOperations.query.filter_by(id_grp_operation=id_grp_operation).filter(tOperations.amount<0).first()
    form = formTransfer(request.form)
    # Get choices and form
    if dictOperationTypes.query.get(credit.id_type_operation).label == 'Remboursement de frais' :
        type_operation = 'Refund'
        print('refund')
        ToAccounts = tAccounts.query.filter_by(is_personnal=True)
        id_type_operation = dictOperationTypes.query.filter_by(label = 'Remboursement de frais').one().id_type_operation
        id_category = dictCategories.query.filter_by(cd_category=110).one().id_category
    elif dictOperationTypes.query.get(credit.id_type_operation).label == 'Transaction interne' :
        type_operation = 'Internal'
        ToAccounts = tAccounts.query.filter_by(is_personnal=False)
        id_type_operation = dictOperationTypes.query.filter_by(label = 'Transaction interne').one().id_type_operation
        id_category = dictCategories.query.filter_by(cd_category=100).one().id_category
    # Filter debitable accounts
    FromAccounts = tAccounts.query.filter_by(is_personnal=False)
    form.from_id_account.choices = [('', '-- Sélectionnez un compte débiteur --')] + [(FromAccount.id_account, FromAccount.name) for FromAccount in FromAccounts]
    # Filter creditable accounts
    form.to_id_account.choices = [('', '-- Sélectionnez un compte créditeur --')] + [(ToAccount.id_account, ToAccount.name) for ToAccount in ToAccounts]
    # Payment method
    PaymentMethods = dictPaymentMethods.query.all()
    form.id_payment_method.choices = [('', '-- Sélectionnez un moyen de paiement --')] + [(PaymentMethod.id_payment_method, PaymentMethod.label) for PaymentMethod in PaymentMethods]
    # Pre-load data
    form.process(
        obj=credit, 
        detail_transfer=credit.detail_operation, 
        from_id_account=debit.id_account,
        to_id_account=credit.id_account)
    # Update data
    if request.method == 'POST' and form.validate() :
        # id_grp_operation unchanged
        #Libelle
        credit.name = request.form['name']
        debit.name= request.form['name']
        # Details
        credit.detail_operation = request.form['detail_transfer']
        debit.detail_operation = request.form['detail_transfer']
        # id_type_operation unchanged
        # Effective_date
        credit.effective_date = request.form['effective_date']
        debit.effective_date =request.form['effective_date']
        # Amount
        credit.amount = getDecimal(request.form.get('amount'))
        debit.amount = -getDecimal(request.form.get('amount'))
        # Payment method
        credit.id_payment_method = getChoiceOrNone(request.form['id_payment_method'])
        debit.id_payment_method =getChoiceOrNone(request.form['id_payment_method'])
        # id_account
        credit.id_account = request.form['to_id_account']
        debit.id_account = request.form['from_id_account']
        # let None as id_budget
        # let id_category unchanged
        # let None as file
        # let false as pointed
        # id_digitiser
        credit.meta_id_digitiser = current_user.id_user
        debit.meta_id_digitiser =current_user.id_user
        db.session.commit()
        return redirect(url_for('operations'))
    # return form
    return render_template('operations/add_or_update_transfer.html', form=form, Transfert=id_grp_operation, Type=type_operation)



# Suppression
@app.route('/operations/transfer/<id_grp_operation>/delete', methods=['GET', 'POST'])
@login_required
def deleteTransfer(id_grp_operation): 
    operations=tOperations.query.filter_by(id_grp_operation=id_grp_operation)
    for operation in operations :
        db.session.delete(operation)
        db.session.commit()
    return redirect(url_for('operations'))


###############
# Engagements #
###############
# Liste
@app.route('/commitments')
@login_required
def commitments():
    #Pagination
    Commitments = vOperations.query.filter(vOperations.type_operation == 'Engagement').order_by(vOperations.operation_date.desc()).all()
    return render_template('operations/commitments_list.html', Commitments=Commitments)

# Ajout
@app.route('/commitment/add', methods=['GET', 'POST'])
@login_required
def addCommitment():
    #Get choices and form
    id_type_operation = dictOperationTypes.query.filter_by(label = 'Engagement').one().id_type_operation
    form = formCommitment(request.form)
    # Form Choices
    # accounts
    Accounts = tAccounts.query.filter_by(is_personnal=False)
    form.id_account.choices = [('', '-- Sélectionnez un compte --')] + [(Account.id_account, Account.name) for Account in Accounts]
    # Budget
    activeBudgets = tBudgets.query.filter_by(active=True)
    form.id_budget.choices = [('', '-- Sélectionnez un budget --')] + [(activeBudget.id_budget, activeBudget.name) for activeBudget in activeBudgets]
    # Category
    id_type_depenses = dictOperationTypes.query.filter_by(label = 'Dépense').one().id_type_operation
    Categories = dictCategories.query.filter(dictCategories.id_type_operation == id_type_depenses, dictCategories.seizable == True).all()
    form.id_category.choices = [('', '-- Sélectionnez une catégorie --')] + [(category.id_category, str(category.cd_category)+" - "+category.label) for category in Categories]
    # Commit form
    if request.method == 'POST' and form.validate() :
        Commitment = tOperations(
            None, #None as id_grp_operation
            request.form['name'],
            request.form['detail_operation'],
            id_type_operation,
            request.form['operation_date'],
            None,
            -getDecimal(request.form.get('amount')),
            None,
            getChoiceOrNone(request.form['id_account']),
            getChoiceOrNone(request.form['id_budget']),
            getChoiceOrNone(request.form['id_category']),
            getFileUrl('uploaded_file'),
            bool('false'),
            current_user.id_user
        )
        db.session.add(Commitment)
        db.session.commit()
        return redirect(url_for('commitments'))
    # Return form
    return render_template('operations/add_or_update_commitment.html', form=form, Operation=None)

# Modification
@app.route('/commitment/edit/<id_operation>', methods=['GET','POST'])
@login_required
def updateCommitment(id_operation):
    # pre-loaded form
    Operation = tOperations.query.get(id_operation)
    #Get choices and form
    id_type_operation = dictOperationTypes.query.filter_by(label = 'Engagement').one().id_type_operation
    form = formCommitment(request.form, obj=Operation)
    # Form Choices
    # accounts
    Accounts = tAccounts.query.filter_by(is_personnal=False)
    form.id_account.choices = [('', '-- Sélectionnez un compte --')] + [(Account.id_account, Account.name) for Account in Accounts]
    form.id_account.default=Operation.id_account
    # Budget
    activeBudgets = tBudgets.query.filter_by(active=True)
    form.id_budget.choices = [('', '-- Sélectionnez un budget --')] + [(activeBudget.id_budget, activeBudget.name) for activeBudget in activeBudgets]
    form.id_budget.default=Operation.id_budget
    # Category
    id_type_depenses = dictOperationTypes.query.filter_by(label = 'Dépense').one().id_type_operation
    Categories = dictCategories.query.filter(dictCategories.id_type_operation == id_type_depenses, dictCategories.seizable == True).all()
    form.id_category.choices = [('', '-- Sélectionnez une catégorie --')] + [(category.id_category, str(category.cd_category)+" - "+category.label) for category in Categories]
    form.id_category.default=Operation.id_category
    # update
    if request.method == 'POST' and form.validate():
        # Let None as id_grp_operation
        Operation.name = request.form['name']
        Operation.detail_operation = request.form['detail_operation']
        Operation.operation_date = request.form['operation_date']
        Operation.effective_date = request.form['effective_date']
        Operation.amount = -getDecimal(request.form.get('amount'))
        Operation.id_account = getChoiceOrNone(request.form['id_account'])
        Operation.id_budget = getChoiceOrNone(request.form['id_budget'])
        Operation.id_category = getChoiceOrNone(request.form['id_category'])
        if not request.form.get('keep_file'):
            Operation.uploaded_file = getFileUrl('uploaded_file')
        Operation.meta_id_digitiser = current_user.id_user
        db.session.commit()
        return redirect(url_for('commitments'))
    return render_template('operations/add_or_update_commitment.html', form=form, Operation=Operation)

# Conversions
@app.route('/commitment/convert/<id_operation>', methods=['GET','POST'])
@login_required
def convertCommitment(id_operation):
    # pre-loaded form
    Operation = tOperations.query.get(id_operation)
    #Get choices and form
    id_type_operation = dictOperationTypes.query.filter_by(label = 'Dépense').one().id_type_operation
    form = formMovement(request.form, obj=Operation)
    # Form Choices
    # accounts
    Accounts = tAccounts.query.filter_by(is_personnal=False)
    form.id_account.choices = [('', '-- Sélectionnez un compte --')] + [(Account.id_account, Account.name) for Account in Accounts]
    form.id_account.default=Operation.id_account
    # Budget
    activeBudgets = tBudgets.query.filter_by(active=True)
    form.id_budget.choices = [('', '-- Sélectionnez un budget --')] + [(activeBudget.id_budget, activeBudget.name) for activeBudget in activeBudgets]
    form.id_budget.default=Operation.id_budget
    # Category
    id_type_depenses = dictOperationTypes.query.filter_by(label = 'Dépense').one().id_type_operation
    Categories = dictCategories.query.filter(dictCategories.id_type_operation == id_type_depenses, dictCategories.seizable == True).all()
    form.id_category.choices = [('', '-- Sélectionnez une catégorie --')] + [(category.id_category, str(category.cd_category)+" - "+category.label) for category in Categories]
    form.id_category.default=Operation.id_category
    # Payment method
    PaymentMethods = dictPaymentMethods.query.all() # TODO filtrer avec la cor.
    form.id_payment_method.choices = [('', '-- Sélectionnez un moyen de paiement --')] + [(PaymentMethod.id_payment_method, PaymentMethod.label) for PaymentMethod in PaymentMethods]
    # update
    if request.method == 'POST' and form.validate():
        # Let None as id_grp_operation
        Operation.name = request.form['name']
        Operation.detail_operation = request.form['detail_operation']
        Operation.id_type_operation = id_type_operation
        Operation.operation_date = request.form['operation_date']
        Operation.effective_date = request.form['effective_date']
        Operation.amount = -getDecimal(request.form.get('amount'))
        Operation.id_payment_method = getChoiceOrNone(request.form['id_payment_method'])
        Operation.id_account = getChoiceOrNone(request.form['id_account'])
        Operation.id_budget = getChoiceOrNone(request.form['id_budget'])
        Operation.id_category = getChoiceOrNone(request.form['id_category'])
        Operation.uploaded_file = getFileUrl('uploaded_file')
        Operation.meta_id_digitiser = current_user.id_user
        db.session.commit()
        return redirect(url_for('operations'))
    return render_template('operations/add_or_update_movement.html', form=form, Operation=Operation, type_operation="Dépense", Convert=True)


# Suppression
@app.route('/commitment/<id_operation>/delete', methods=['GET', 'POST'])
@login_required
def deleteCommitment(id_operation): 
    operation=tOperations.query.get(id_operation)
    db.session.delete(operation)
    db.session.commit()
    return redirect(url_for('commitments'))


#############
### Admin ###
#############
### Members ###
@app.route('/admin/members', methods=['GET'])
@login_required
def members():
    Members=tMembers.query.all()
    return render_template('admin/members/members_list.html', Members=Members)

@app.route('/admin/member/add', methods=['GET','POST'])
@login_required
def addMember():
    form = formMember(request.form)
    if request.method == 'POST' and form.validate():
        member = tMembers(
            request.form['member_name'],
            request.form['member_role'],
            bool(request.form.get('is_employed')),
            bool(request.form.get('active'))
            )
        db.session.add(member)
        db.session.commit()
        return redirect(url_for('members'))
    return render_template('admin/members/add_or_update_member.html', form=form, Member=None, active=True, is_employed=False)

@app.route('/admin/member/edit/<id_member>', methods=['GET','POST'])
@login_required
def updateMember(id_member):
    member = tMembers.query.get(id_member)
    form = formMember(request.form, obj=member)
    if request.method == 'POST' and form.validate():
        member.member_name = request.form['member_name']
        member.member_role = request.form['member_role']
        member.is_employed = bool(request.form.get('is_employed'))
        member.active = bool(request.form.get('active'))
        db.session.commit()
        return redirect(url_for('members'))
    return render_template('admin/members/add_or_update_member.html', form=form, Member=member, active=member.active, is_employed=member.is_employed)




### Categories ###
# List categories
@app.route('/admin/categories')
@login_required
def categories():
    Depenses=dictCategories.query.filter_by(id_type_operation = dictOperationTypes.query.filter_by(label='Dépense').one().id_type_operation).all()
    Recettes=dictCategories.query.filter_by(id_type_operation = dictOperationTypes.query.filter_by(label='Recette').one().id_type_operation).all()
    Benevolats=dictCategories.query.filter_by(id_type_operation = dictOperationTypes.query.filter_by(label='Valorisation du bénévolat').one().id_type_operation).all()
    Transferts=dictCategories.query.filter_by(id_type_operation = dictOperationTypes.query.filter_by(label='Transaction interne').one().id_type_operation).all()
    return render_template('admin/categories/categories_list.html', Depenses = Depenses, Recettes=Recettes, Benevolats=Benevolats,Transferts=Transferts)


###############
### Funders ###
###############
# List funders
@app.route('/funders', methods=['GET'])
@login_required
def funders():
    return render_template('funders/funders_list.html', Funders = tFunders.query.all() )

# Detail funder
@app.route('/funders/detail/<id_funder>', methods=['GET'])
@login_required
def detailFunder(id_funder):
    return render_template('funders/details_funder.html', Funder = tFunders.query.get(id_funder), Budgets=vBudgets.query.filter_by(id_funder=id_funder).all() )

# Add funder
@app.route('/funders/add', methods=['GET', 'POST'])
@login_required
def addFunder():
    form = formFunder(request.form)
    if request.method == 'POST' and form.validate():
        funder = tFunders(
            request.form['name'], 
            request.form['code'], 
            request.form['logo_url'], 
            request.form['address'], 
            request.form['city'], 
            request.form['zip_code'], 
            request.form['comment'], 
            bool(request.form.get('active'))
        )
        db.session.add(funder)
        db.session.commit()
        return redirect('/funders')
    return render_template('funders/add_or_update_funder.html', form=form, funder=None, active=None)

# Edit funder
@app.route('/funders/edit/<id_funder>', methods=['GET', 'POST'])
@login_required
def updateFunder(id_funder):
    funder = tFunders.query.get(id_funder)
    form = formFunder(request.form, obj=funder)
    if request.method == 'POST' and form.validate():
        funder.name=request.form['name']
        funder.code=request.form['code']
        funder.logo_url=request.form['logo_url']
        funder.address=request.form['address']
        funder.city=request.form['city']
        funder.zip_code=request.form['zip_code']
        funder.comment=request.form['comment']
        funder.active=bool(request.form.get('active'))
        db.session.commit()
        return redirect('/funders')
    return render_template('funders/add_or_update_funder.html', form=form, funder=funder, active=tFunders.query.get(id_funder).active)

# Delete funder
@app.route('/funders/delete/<id_funder>', methods=['GET', 'POST'])
@login_required
def deleteFunder(id_funder):
    current_funder=tFunders.query.get(id_funder)
    db.session.delete(current_funder)
    db.session.commit()
    return redirect('/funders')


###############
### PAYROLL ###
###############

@app.route('/employees/payrolls')
@login_required
def payrolls(id_member=None):
    if id_member:
        payrolls = vPayrolls.query.filter_by(id_member=id_member).all()
    else :
        payrolls = vPayrolls.query.all()
    return render_template('payrolls/payrolls_list.html', payrolls=payrolls)


@app.route('/employees/payrolls/add', methods=['GET', 'POST'])
@login_required
def addPayroll():
    form = formPayroll(request.form)
    # Get employees
    Members = tMembers.query.filter_by(is_employed=True)
    form.id_member.choices = [(Member.id_member, Member.member_name) for Member in Members]
    if request.method == 'POST' and form.validate():
        payroll = corMemberPayroll(
            getChoiceOrNone(request.form['id_member']), 
            request.form['date_min_period'], 
            request.form['date_max_period'], 
            getDecimal(request.form['member_net_gain']), 
            getDecimal(request.form['member_charge_amount']), 
            getDecimal(request.form['employer_charge_amount']), 
            getDecimal(request.form['real_worked_days'])
            )
        db.session.add(payroll)
        db.session.commit()
        return redirect(url_for('payrolls'))
    return render_template('payrolls/add_or_update_member_payroll.html', form=form, payroll=None, Members=Members)


@app.route('/employees/payrolls')
@login_required
def payrollBudget(id_member=None):
    if id_member:
        payrolls = vPayrolls.query.filter_by(id_member=id_member).all()
    else :
        payrolls = vPayrolls.query.all()
    return render_template('payrolls/payrolls_list.html', payrolls=payrolls)


@app.route('/employees/payroll_budget/add', methods=['GET', 'POST'])
@login_required
def addPayrollBudget():
    form = formPayrollBudget(request.form)
    # Get employees
    Members = tMembers.query.filter_by(is_employed=True)
    form.id_member.choices = [(Member.id_member, Member.member_name) for Member in Members]
    # Get budgets
    Budgets = tBudgets.query.filter_by(active=True)
    form.id_budget.choices = [(Budget.id_budget, Budget.name) for Budget in Budgets]
    if request.method == 'POST' and form.validate():
        payrollBudget = corPayrollBudget(
            getChoiceOrNone(request.form['id_budget']), 
            getChoiceOrNone(request.form['id_member']), 
            request.form['date_min_period'], 
            request.form['date_max_period'], 
            getDecimal(request.form['nb_days_allocated']), 
            getDecimal(request.form['fixed_cost'])
            )
        db.session.add(payrollBudget)
        db.session.commit()
        return redirect(url_for('payrollBudget'))
    return render_template('payrolls/add_or_update_allocation_payroll_budget.html', form=form, payrollBudget=None, Members=Members, Budgets=Budgets)




###################
### EXPORTS PDF ###
###################

# Export as pdf
@app.route('/results/pdf')
@login_required
def resultsPDF():
    html = render_template('results_pdf.html')
    css = '../static/css/bootstrap/bootstrap.css'
    options = {"enable-local-file-access": None}
    pdf = pdfkit.from_string(html, False, options=options)
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=export_bilan.pdf"
    return response





###############
### RESULTS ###
###############

# Request results
@app.route('/results')
@login_required
def results():
    return render_template('results/results.html')



###########################
### Frais kilométriques ###
###########################
# TODO





#################################
### Valorisation de bénévolat ###
#################################
# Ajout
@app.route('/volunteering/add')
@login_required
def addBenevolat():
    return render_template('operations/add_or_update_benevolat.html')

# Modification

# Détail

# Suppression


