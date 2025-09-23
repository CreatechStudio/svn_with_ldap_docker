from ldap3 import Server, Connection, ALL

#read from .env
import os
from dotenv import load_dotenv
load_dotenv()
LDAP_URI = os.getenv("LDAP_URI")
BIND_DN = os.getenv("BIND_DN")
BIND_PW = os.getenv("BIND_PW")
BASE_DN = os.getenv("BASE_DN")

AUTHZ_FILE = "conf/authz"

def fetch_all_groups_from_ldap():
    server = Server(LDAP_URI, get_info=ALL)
    conn = Connection(server, BIND_DN, BIND_PW, auto_bind=True)
    
    conn.search(
        search_base=BASE_DN,
        search_filter="(objectClass=groupOfNames)",
        attributes=["sAMAccountName"]
    )

    groups_map = {}
    if conn.entries:
        for entry in conn.entries:
            group_dn = str(entry.entry_dn)
            group_name = str(entry["sAMAccountName"])
            groups_map[group_name] = group_dn
            
    conn.unbind()
    return groups_map

def fetch_group_members(group_dn):
    server = Server(LDAP_URI, get_info=ALL)
    conn = Connection(server, BIND_DN, BIND_PW, auto_bind=True)

    conn.search(
        search_base=group_dn,
        search_filter="(objectClass=groupOfNames)",
        attributes=["member"],
    )

    if not conn.entries:
        return []

    members_dns = conn.entries[0]["member"].values
    usernames = []

    for dn in members_dns:
        conn.search(
            search_base=dn,
            search_filter="(objectClass=person)",
            attributes=["sAMAccountName"],
        )
        if conn.entries:
            usernames.append(str(conn.entries[0]["sAMAccountName"]))
    conn.unbind()
    return usernames

def update_authz(groups_map):
    try:
        with open(AUTHZ_FILE, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    lines = content.split('\n')
    new_lines = []
    in_groups_section = False
    
    for line in lines:
        if line.strip() == '[groups]':
            in_groups_section = True
            new_lines.append('[groups]')
            for group_name, users in groups_map.items():
                new_lines.append(f"{group_name} = {', '.join(users)}")
            continue
        elif line.strip().startswith('[') and line.strip().endswith(']'):
            in_groups_section = False
        
        if not in_groups_section:
            new_lines.append(line)

    if '[groups]' not in content:
        new_lines.insert(0, '')
        new_lines.insert(0, '\n'.join([f"{group_name} = {', '.join(users)}" for group_name, users in groups_map.items()]))
        new_lines.insert(0, '[groups]')

    with open(AUTHZ_FILE, "w") as f:
        f.write('\n'.join(new_lines))


if __name__ == "__main__":
    all_groups = fetch_all_groups_from_ldap()
    groups_map = {}
    for local_name, dn in all_groups.items():
        users = fetch_group_members(dn)
        groups_map[local_name] = users
        print(f"同步组 {local_name}: {users}")

    update_authz(groups_map)
    print(f"已更新 {AUTHZ_FILE}")