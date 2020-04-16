route_count = 0
float_count = 0
if_id= 0
snmp_trap_id = 0

res=""
dict_advhc={}
dict_reals={}
dict_group={}
dict_vip={}
dict_pmap={}
dict_cippersist={}
dict_virt={}
dict_route={}
dict_interface = {}
dict_float = {}
dict_nwcls = {}
dict_sys = {'ssnmp':{}}
dict_redirect1 = {}
dict_redirect2 = {}

list_gw = []
list_advif = []
log1banner='''
##########################################################
# Commands unsupported by script but supported by Alteon #
# Syntax :                                               #
# Object type                                            # 
# Object name - as appears in ACE Config                 #
# Issue/unparsable line in ACE config                    #
##########################################################
'''
log2banner='''
#####################################################################
# Configuration skipped by the script - please review manually      #
#####################################################################
'''

convert_svc = {
	'www': 'http',
	'https': 'https'
}

convert_dport = {
	'www': '80',
	'https': '443'
}

metricDict = {}

