import re
# DSHELL=/bin/bash
# DHOME=/home
# GROUPHOMES=no
# LETTERHOMES=no
# SKEL=/etc/skel
# FIRST_SYSTEM_UID=100
# LAST_SYSTEM_UID=999
# FIRST_SYSTEM_GID=100
# LAST_SYSTEM_GID=999
# FIRST_UID=1000
# LAST_UID=29999
# FIRST_GID=1000
# LAST_GID=29999
# USERGROUPS=yes
# USERS_GID=100
# DIR_MODE=0755
# SETGID_HOME=no
# QUOTAUSER=""
# SKEL_IGNORE_REGEX="dpkg-(old|new|dist|save)"
# EXTRA_GROUPS="dialout cdrom floppy audio video plugdev users"
# ADD_EXTRA_GROUPS=1
# NAME_REGEX="^[a-z][-a-z0-9_]*\$"


addUserProperties={'DSHELL':None,'DHOME':None,'GROUPHOMES':None,'LETTERHOMES':None,'SKEL':None,
'FIRST_SYSTEM_UID':None,'LAST_SYSTEM_UID':None,'FIRST_SYSTEM_GID':None,'LAST_SYSTEM_GID':None,
'FIRST_UID':None,'LAST_UID':None,'FIRST_GID':None,'LAST_GID':None,'USERGROUPS':None,'USERS_GID':None,
'DIR_MODE':None,'SETGID_HOME':None,'QUOTAUSER':None,'SKEL_IGNORE_REGEX':None,'EXTRA_GROUPS':None,
'ADD_EXTRA_GROUPS':None,'NAME_REGEX':None}

def getAddUserProperties(conf,properties):
	for l in open(conf,'r').readlines():
		for k in properties.keys():
			if re.match(k+'=',l):
				propertieValue=l.strip('\n').split('=')[1]
				if propertieValue == '\"\"':
					propertieValue=None
				properties[k]=propertieValue
				break

	return properties

addUserProperties=getAddUserProperties('/etc/adduser.conf',addUserProperties)
print len(addUserProperties.keys())