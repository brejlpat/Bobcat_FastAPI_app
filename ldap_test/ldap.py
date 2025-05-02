from ldap3 import Server, Connection, ALL, NTLM

# Active Directory server and user's credentials
server_address = 'ldap://corp.doosan.com'  # Example: ldap://example.com or ldaps://example.com
username = 'DSG\\patrikbrejla'  # Domain and username
password = 'password'  # User's password

# Create the server and connection objects
server = Server(server_address, use_ssl=True, get_info=ALL)
conn = Connection(server, user=username, password=password, authentication=NTLM, auto_bind=True)

if conn.bind():
    print('Successfully bound to the server.')
else:
    print('Failed to bind to the server.')

# Define the base distinguished name
base_dn = 'DC=corp,dc=doosan,dc=com'

# Perform an LDAP search
search_filter = '(cn=patrikbrejla)'
conn.search(base_dn, search_filter, attributes=['cn', 'givenName', 'sn', 'mail'])

# Print the results
for entry in conn.entries:
    print(entry)

# Unbind the connection
conn.unbind()
