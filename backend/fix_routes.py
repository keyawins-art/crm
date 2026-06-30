with open('app/api/crm.py', 'r') as f:
    lines = f.readlines()

# Find dynamic route start
dynamic_route_idx = -1
for i, line in enumerate(lines):
    if '@router.post("/{module_name}' in line or '@router.get("/{module_name}' in line:
        dynamic_route_idx = i
        break

# Find specific lead routes start (timeline, notes, activities)
timeline_route_idx = -1
for i, line in enumerate(lines):
    if '@router.get("/leads/{id}/timeline"' in line:
        timeline_route_idx = i
        break

users_idx = -1
for i, line in enumerate(lines):
    if line.strip() == '# Users':
        users_idx = i
        break

if dynamic_route_idx != -1 and timeline_route_idx != -1 and users_idx != -1:
    if timeline_route_idx > dynamic_route_idx:
        # We need to move the block from timeline_route_idx to users_idx
        # to just before dynamic_route_idx
        block_to_move = lines[timeline_route_idx:users_idx]
        
        # Remove the block from its original position
        del lines[timeline_route_idx:users_idx]
        
        # Insert it before dynamic routes (have to recalculate dynamic index since we deleted lines?
        # Actually timeline_route_idx > dynamic_route_idx so dynamic index is unchanged)
        lines = lines[:dynamic_route_idx] + block_to_move + lines[dynamic_route_idx:]
        
        with open('app/api/crm.py', 'w') as f:
            f.writelines(lines)
        print("Moved specific routes above generic routes successfully!")
    else:
        print("Specific routes are already above generic routes.")
else:
    print("Could not find all indices.", dynamic_route_idx, timeline_route_idx, users_idx)
