import re

def generate_crud_block(module_name, model_class, schema_create, schema_read, schema_update, permissions_prefix):
    rls_code = f"""
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr({model_class}, 'owner_id'):
            query = query.filter({model_class}.owner_id == current_user.id)
        elif hasattr({model_class}, 'assigned_to_id'):
            if hasattr({model_class}, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_({model_class}.assigned_to_id == current_user.id, {model_class}.created_by_id == current_user.id))
            else:
                query = query.filter({model_class}.assigned_to_id == current_user.id)
        elif hasattr({model_class}, 'created_by_id'):
            query = query.filter({model_class}.created_by_id == current_user.id)
"""

    return f'''
# {module_name.capitalize()}
@router.post("/{module_name}", response_model={schema_read}, status_code=status.HTTP_201_CREATED)
def create_{module_name[:-1]}(
    payload: {schema_create},
    current_user: User = Depends(require_permission("{permissions_prefix}:create")),
    db: Session = Depends(get_db),
):
    obj = {model_class}(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{module_name}", response_model=List[{schema_read}])
def list_{module_name}(
    current_user: User = Depends(require_permission("{permissions_prefix}:read")),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: Optional[str] = None,
):
    query = db.query({model_class})
    if not include_deleted:
        query = query.filter({model_class}.is_deleted == False)
{rls_code}
    if search:
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr({model_class}, field):
                search_filters.append(getattr({model_class}, field).ilike(f"%{{search}}%"))
        if search_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*search_filters))

    return query.offset(skip).limit(limit).all()


@router.get("/{module_name}/{{id}}", response_model={schema_read})
def get_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:read")),
    db: Session = Depends(get_db),
):
    query = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == False)
{rls_code}
    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
    return obj


@router.put("/{module_name}/{{id}}", response_model={schema_read})
def update_{module_name[:-1]}(
    id: UUID,
    payload: {schema_update},
    current_user: User = Depends(require_permission("{permissions_prefix}:update")),
    db: Session = Depends(get_db),
):
    query = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == False)
{rls_code}
    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{module_name}/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    query = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == False)
{rls_code}
    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    db.commit()


@router.delete("/{module_name}/{{id}}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:delete")),
    db: Session = Depends(get_db),
):
    query = db.query({model_class}).filter({model_class}.id == id)
{rls_code}
    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found")
        
    db.delete(obj)
    db.commit()


@router.post("/{module_name}/{{id}}/restore", response_model={schema_read})
def restore_{module_name[:-1]}(
    id: UUID,
    current_user: User = Depends(require_permission("{permissions_prefix}:update")),
    db: Session = Depends(get_db),
):
    query = db.query({model_class}).filter({model_class}.id == id, {model_class}.is_deleted == True)
{rls_code}
    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="{model_class} not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    db.commit()
    db.refresh(obj)
    return obj
'''

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
    UserCreate, UserRead
)"""
content = re.sub(imports_pattern, replace_imports, content, flags=re.DOTALL)

# Delete existing routes from # Accounts down to # Users
start_idx = content.find('# Accounts')
if start_idx != -1:
    header = content[:start_idx]
    
    new_blocks = []
    for mod in modules:
        new_blocks.append(generate_crud_block(*mod))
        
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
