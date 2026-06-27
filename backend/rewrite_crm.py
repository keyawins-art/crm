import re

def generate_crud_block(module_name, model_class, schema_create, schema_read, schema_update, permissions_prefix):
    return f'''
# {module_name.capitalize()}
@{`router`}.post("/{module_name}", response_model={schema_read}, status_code=status.HTTP_201_CREATED)
def create_{module_name[:-1]}(
    payload: {schema_create},
    current_user: User = Depends(require_permission("{permissions_prefix}:create")),
    db: Session = Depends(get_db),
):
    obj = {model_class}(**payload.model_dump(exclude_none=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@{`router`}.get("/{module_name}", response_model=List[{schema_read}])
def list_{module_name}(
    current_user: User = Depends(require_permission("{permissions_prefix}:read")),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
):
    query = db.query({model_class})
    if not include_deleted:
        query = query.filter({model_class}.is_deleted == False)
    return query.offset(skip).limit(limit).all()


@{`router`}.get("/{module_name}/{{id}}", response_model={schema_read})
def get_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:read")),
    db: Session = Depends(get_db),
):
    obj = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == False).first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
    return obj


@{`router`}.put("/{module_name}/{{id}}", response_model={schema_read})
def update_{module_name[:-1]}(
    id: UUID,
    payload: {schema_update},
    current_user: User = Depends(require_permission("{permissions_prefix}:update")),
    db: Session = Depends(get_db),
):
    obj = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == False).first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    db.commit()
    db.refresh(obj)
    return obj


@{`router`}.delete("/{module_name}/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    obj = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == False).first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    db.commit()


@{`router`}.delete("/{module_name}/{{id}}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:delete")),
    db: Session = Depends(get_db),
):
    obj = db.query({model_class}).filter({model_class}.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
        
    db.delete(obj)
    db.commit()


@{`router`}.post("/{module_name}/{{id}}/restore", response_model={schema_read})
def restore_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:update")),
    db: Session = Depends(get_db),
):
    obj = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == True).first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    db.commit()
    db.refresh(obj)
    return obj
'''.replace('`router`', 'router')

modules = [
    ("accounts", "Account", "AccountCreate", "AccountRead", "AccountUpdate", "accounts"),
    ("contacts", "Contact", "ContactCreate", "ContactRead", "ContactUpdate", "contacts"),
    ("leads", "Lead", "LeadCreate", "LeadRead", "LeadUpdate", "leads"),
    ("products", "Product", "ProductCreate", "ProductRead", "ProductUpdate", "products"),
    ("opportunities", "Opportunity", "OpportunityCreate", "OpportunityRead", "OpportunityUpdate", "opportunities"),
    ("quotations", "Quotation", "QuotationCreate", "QuotationRead", "QuotationUpdate", "quotations"),
]

with open('app/api/crm.py', 'r') as f:
    content = f.read()

# Update imports
imports_pattern = r'from app\.schemas\.crm import \((.*?)\)'
def replace_imports(match):
    return """from app.schemas.crm import (
    AccountCreate, AccountRead, AccountUpdate,
    ContactCreate, ContactRead, ContactUpdate,
    LeadCreate, LeadRead, LeadUpdate,
    OpportunityCreate, OpportunityRead, OpportunityUpdate,
    ProductCreate, ProductRead, ProductUpdate,
    QuotationCreate, QuotationRead, QuotationUpdate,
    UserCreate, UserRead, UserUpdate
)"""
content = re.sub(imports_pattern, replace_imports, content, flags=re.DOTALL)

# Delete existing routes from # Accounts down to # Users (keep users for now or rewrite it)
# Find the start of # Accounts
start_idx = content.find('# Accounts')
if start_idx != -1:
    header = content[:start_idx]
    
    new_blocks = []
    for mod in modules:
        new_blocks.append(generate_crud_block(*mod))
        
    # Append the users block which we'll just keep as is for now, but we need to fetch it from old content
    users_start = content.find('# Users')
    if users_start != -1:
        users_block = content[users_start:]
    else:
        users_block = ""
        
    new_content = header + "\n".join(new_blocks) + "\n\n" + users_block
    
    with open('app/api/crm.py', 'w') as f:
        f.write(new_content)
    print("Rewritten successfully")
else:
    print("Could not find '# Accounts'")
