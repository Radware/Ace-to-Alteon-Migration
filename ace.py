#! python
# version 0.1
import re, sys, json
from global_variables import *

file=open(sys.argv[1], 'r')
output=open(sys.argv[1]+"_output.txt", "w+")
leftovers=open(sys.argv[1]+"_leftovers.txt", "w+")
leftovers.write(log2banner)
log=open(sys.argv[1]+"_log.txt", "w+")
log.write(log1banner)
text=file.read()
### Parsers ###

for advhc in re.findall('(^probe.+\n(  .+\n)+)', text, re.MULTILINE):
	str_advhc = ''.join(advhc[:-1]).replace('\(\'', '').replace('\'\)', '')
	arr_advhc = str_advhc.splitlines()
	junk, hctype, name=arr_advhc[0].split()
	name = name+" "+hctype.upper()
	if hctype=='http':
		dict_advhc.update({name: { }, name+"/http":{}})
	else:
		dict_advhc.update({name: {}})

	for line in arr_advhc[1:]:
		if line[2:6]=="port":
			dict_advhc[name].update({'dport': line[7:]})
		elif line[2:10]=="interval":
			dict_advhc[name].update({'inter': line[11:], 'timeout': line[11:]})
		elif line[2:21]=="passdetect interval":
			dict_advhc[name].update({'downtime': line[22:]})
		elif line[2:15]=="expect status":
			dict_advhc[name+"/http"].update({'response': line.split()[2]+ " none"})
		elif line[2:14]=="expect regex":
			string_check= re.compile('[.$^*()?+\\|{}\[\]]')
			if string_check.search(line[15:]):
				log.write("\nObject type = Health Check\nObject Name = %s\nIssue = Encountered a regex patternt in expected response (%s).\nPlease address manually!\n" % (name, line[15:]) )
			else:
				dict_advhc[name+"/http"].update({'response 200 incl': line.split()[2]})
		elif line[2:16]=="request method":
			l=iter(line.replace('request','').split())
			for item in l:
				if item=='method':
					dict_advhc[name+"/http"].update({'method': next(l)})
				elif item=='url':
					dict_advhc[name+"/http"].update({'path': "\""+next(l)[1:]+"\""})
				else:
					log.write("\nObject type = Health Check\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
		elif line[2:18]=="passdetect count":
			dict_advhc[name].update({'restr': line.split()[2]})
		else:
			log.write("\nObject type = Health Check\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
	text = re.sub(str_advhc[:-1], '', text)
#end of probe

for real in re.findall('(^rserver .+\n(  .+\n)+)', text, re.MULTILINE):
	str_real = ''.join(real[:-1]).replace('\(\'', '').replace('\'\)', '')
	arr_real = str_real.splitlines()
	if arr_real[0][0:12] == "rserver host":
		name=arr_real[0][13:]
		dict_reals.update({name:{}})
		for line in arr_real[1:]:
			if line[2:12] == "ip address":
				dict_reals[name].update({'rip': line[13:]})
			elif line[2:11] == 'inservice':
				dict_reals[name].update({'ena':''})
			else:
				log.write("\nObject type = Real\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
		if not 'ena' in dict_reals[name]:
			dict_reals[name].update({'dis':''})
	elif arr_real[0][0:16] == "rserver redirect":
		name=arr_real[0][17:]
		dict_redirect1.update({name:{}})
		for line in arr_real[1:]:
			if line[2:21] == "webhost-redirection":
				dict_redirect1[name].update({'loc': line[22:].split()[0]})
	text = re.sub(str_real[:-1], '', text)
#end of real

for group in re.findall('(^serverfarm .+\n(  .+\n)+)', text, re.MULTILINE):
	tmp_real_dict={}
	str_group = ''.join(group[:-1]).replace('\(\'', '').replace('\'\)', '')
	arr_group = str_group.splitlines()
	if arr_group[0][0:15] == "serverfarm host":
		name = arr_group[0][16:]
		redir=0
	elif arr_group[0][0:19] == "serverfarm redirect":
		name = arr_group[0][20:]
		redir=1
	dict_group.update({name:{}})
	c=0
	for line in arr_group[1:]:
		c+=1
		if line[2:9] == "rserver":
			if " " in line[10:]:
				r, p = line[10:].split()
			else:
				p=0
				r=line[10:]
			if p in tmp_real_dict:
				tmp_real_dict[p].append(r)
			else:
				tmp_real_dict.update({p:[r]})
			if not arr_group[c+1].replace(' ', '') == 'inservice':
				log.write("\nObject type = Group\nObject Name = %s\nIssue = Encountered a disabled real server (%s).\nPlease address manually!\n\n" % (name, r) )
		elif line[2:11] == "predictor":
			dict_group[name].update({'metric': line[12:]})
		elif line[2:7] == "probe":
			dict_group[name].update({'health': line[8:]})
		elif line.replace(' ', '') == 'inservice':
			continue
		else:
			log.write("\nObject type = Group\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
	if redir:
		if len(tmp_real_dict[0]) != 1:
			log.write("\nObject type = Group\nObject Name = %s\nIssue = Redirect destination amount is not 1.\nPlease address manually!\n\n" % name )
		elif tmp_real_dict[0][0] in dict_redirect1:
			dict_redirect2.update({name: dict_redirect1[tmp_real_dict[0][0]]})
		else:
			log.write("\nObject type = Group\nObject Name = %s\nIssue = Did not find redirect destination.\nPlease address manually!\n\n" % name )
		dict_group.pop(name, None)
		continue
	if len(tmp_real_dict.keys()) == 0:
		pass
	elif len(tmp_real_dict.keys()) == 1:
		dict_group[name].update({'add': '\n  add '.join(tmp_real_dict[list(tmp_real_dict.keys())[0]])})
		#dict_group[name].update({'add': tmp_real_dict[tmp_real_dict.keys()[0]] })
		pass
	elif len(tmp_real_dict.keys()) == 2:
		log.write("\nObject type = Group\nObject Name = %s\nIssue = Please complete backup group logic.\n\n" % name )
	else:
		log.write("\nObject type = Group\nObject Name = %s\nIssue = Unsupported priority found, full group counfiguration:\n %s\nPlease address manually!\n\n" % (name, str_group) )
	text = re.sub(str_group[:-1], '', text)
	# end of for loop
#end of group


for vip in re.findall('(^class-map .+\n(  .+\n)+)', text, re.MULTILINE):
	str_vip = ''.join(vip[:-1]).replace('\(\'', '').replace('\'\)', '')
	arr_vip = str_vip.splitlines()
	if arr_vip[0][0:19] == "class-map match-all":
		name=arr_vip[0].split()[2]
	elif arr_vip[0][0:25] == "class-map type management":
		log.write("\nObject type = Class-Map\nObject Name = %s\nIssue = Management class-map found\nPlease address manually!\n\n" % arr_vip[0].split()[2] )
		continue
	dict_vip.update({name:{}})
	for line in arr_vip[1:]:
		tmp=line.split()
		if tmp[0]=="description":
			vname=line
		if tmp[1]=="match" and tmp[2]=='virtual-address':
			if tmp[6] in convert_dport:
				dport = convert_dport[tmp[6]]
			else:
				dport = tmp[6]
			if tmp[6] in convert_svc:
				svc = convert_svc[tmp[6]]
			else:
				svc = 'basic-slb'
			dict_vip[name].update({'vip':tmp[3], 'proto':tmp[4], 'dport': dport, 'svc': svc})
		elif tmp[1]=="match" and tmp[2]=="protocol":
			log.write("\nObject type = Class-Map\nObject Name = %s\nIssue = protocol matching found: %s\nPlease address manually!\n\n" % (name, line) )
		else: 
			log.write("\nObject type = Class-Map\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
	text = re.sub(str_vip[:-1], '', text)
	# end of for loop
#end of vip

for cippersist in re.findall('(^sticky .+\n(  .+\n)+)', text, re.MULTILINE):
	str_cippersist = ''.join(cippersist[:-1]).replace('\(\'', '').replace('\'\)', '')
	arr_cippersist = str_cippersist.splitlines()
	tmp=arr_cippersist[0].split()
	if tmp[2]!="255.255.255.255":
		log.write("\nObject type = Source IP\nObject Name = %s\nIssue = Mask different than /32 isn't supported.\nPlease address manually!\n" % name )
	if tmp[4]!="source":
		log.write("\nObject type = Source IP\nObject Name = %s\nIssue = Dest IP persist isn't supported.\nPlease address manually!\n" % name )
	name=tmp[5]
	dict_cippersist.update({name: {'pbind': 'clientip'}})
	for line in arr_cippersist[1:]:
		if line[2:9]=="timeout":
			dict_cippersist[name].update({'ptmout': line[10:]})
		elif line[2:18] == "replicate sticky":
			pass
		elif line[2:12]== "serverfarm":
			if line[13:] in dict_group:
				dict_cippersist[name].update({'group': line[13:]})
			elif line[13:] in dict_redirect2:
				dict_cippersist[name].update({'redirect': dict_redirect2[line[13:]]})
				dict_cippersist[name].update({'action': 'redirect'})
			else:
				log.write("\nObject type = Source IP\nObject Name = %s\nIssue = Group \"%s\" not found.\nPlease address manually!\n" % (name, line[13:]) )
		else:
			log.write("\nObject type = Source IP\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
	text = re.sub(str_cippersist[:-1], '', text)
	# end of for loop
#end cippersist

for pmap1 in re.findall('(^policy-map type management.+\n(  .+\n)+)', text, re.MULTILINE):
	str_pmap1 = ''.join(pmap1[:-1]).replace('\(\'', '').replace('\'\)', '')
	log.write("\nObject type = Management Policy\nObject Name = N/A\nIssue = Encountered an unhandeled command\n %s.\nPlease address manually!\n" % str_pmap1 )

for pmap2 in re.findall('(^policy-map type loadbalance .+\n(  .+\n)+)', text, re.MULTILINE):
	str_pmap2 = ''.join(pmap2[:-1]).replace('\(\'', '').replace('\'\)', '')
	name=str_pmap2.splitlines()[0].split()[4]
	dict_pmap.update({name:{}})
	for cls in re.findall('(^  class .+\n(    .+\n)+)', str_pmap2, re.MULTILINE):
		arr_cls = ''.join(cls[:-1]).replace('\(\'', '').replace('\'\)', '').splitlines()
		if arr_cls[0][8:] != "class-default":
			log.write("\nObject type = LB Policy\nObject Name = %s\nIssue = please verify policy (%s).\nPlease address manually!\n" % (name, line) )
		for line in arr_cls[1:]:
			if line[4:21]=="sticky-serverfarm":
				for x in dict_cippersist[line[22:]]:
					dict_pmap[name].update({x: dict_cippersist[line[22:]][x]})
			elif line[4:14]=="serverfarm":
				dict_pmap[name].update({'group': line[15:]})
			else:
				log.write("\nObject type = LB Policy\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
	text = re.sub(str_pmap2[:-1], '', text)
	# end of for loop
#end pmap2

for pmap in re.findall('(^policy-map multi-match .+\n(  .+\n)+)', text, re.MULTILINE):
	str_pmap = ''.join(pmap[:-1]).replace('\(\'', '').replace('\'\)', '')
	for cls in re.findall('(^  class .+\n(    .+\n)+)', str_pmap, re.MULTILINE):
		arr_cls = ''.join(cls[:-1]).replace('\(\'', '').replace('\'\)', '').splitlines()
		name=arr_cls[0][8:]
		if "    loadbalance vip inservice" in arr_cls:
			dict_virt.update({name: {'ena':''}})
			arr_cls.remove("    loadbalance vip inservice")
		else:
			dict_virt.update({name: {'dis':''}})

		if "    loadbalance vip icmp-reply" in arr_cls:
			arr_cls.remove("    loadbalance vip icmp-reply")
		else:
			# print("Vip should not reply ICMP. please address manually")
			pass
		dict_virt[name].update({'vip':dict_vip[name]['vip']})
		service=name+"/service "+dict_vip[name]['dport']+" "+dict_vip[name]['svc']
		dict_virt.update({service:{}})
		for line in arr_cls[1:]:
			if line[4:22]=="loadbalance policy":
				for x in dict_pmap[line[23:]]:
					dict_virt[service].update({x: dict_pmap[line[23:]][x]})
			elif line[4:20]=="ssl-proxy server":
				pass
			elif line[4:15]=="nat dynamic":
				log.write("\nObject type = LB Policy\nObject Name = %s\nIssue = please validate PIP \"%s\" for virt \"%s .\nPlease address manually!" % (name, line[16:], service.replace('/', '\\n" ')) )
			else:
				log.write("\nObject type = LB Policy\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
	text = re.sub(str_pmap[:-1], '', text)
	# end of for loop
#end pmap

for route in re.findall('^ip route.+\n', text, re.MULTILINE):
	route_count+=1
	text=text.replace(route,'')
	route = route.split()
	if route[2] == "0.0.0.0" and route[3] == "0.0.0.0":
		list_gw.append(route[4])
	else:
		dict_route.update({route_count: { 'dst': route[2], 'mask': route[3], 'gw': route[4] }})
#end pmap


for interface in re.findall('(^interface .+\n(  .+\n)+)', text, re.MULTILINE):
	str_interface = ''.join(interface[:-1]).replace('\(\'', '').replace('\'\)', '')
	arr_interface = str_interface.splitlines()
	vlan=arr_interface[0].split()[2]
	if_id+=1
	dict_interface.update({if_id: {'vlan': vlan}})
	if "  no shutdown" in arr_interface:
		dict_interface[if_id].update({'ena': ''})
		arr_interface.remove("  no shutdown")
	for line in arr_interface[1:]:
		if line[2:13] == "description":
			dict_interface[if_id].update({'descr': '"'+line[14:]+'"'})
		elif line[2:12] == "ip address":
			tmp=line[13:].split()
			dict_interface[if_id].update({'addr': tmp[0], 'mask': tmp[1]})
		elif line[2:17] == "peer ip address":
			tmp=line[18:].split()
			dict_interface[if_id].update({'peer': tmp[0]})
			list_advif.append(if_id)
		elif line[2:7] == "alias":
			float_count+=1
			tmp=line[8:].split()
			dict_float.update({float_count: {'addr': tmp[0], 'if': if_id, 'ena':'', 'ipver': 'v4'}})
		elif line[2:10] == "nat-pool":
			tmp=line[11:].split()
			dict_nwcls.update({ 'name': tmp[0], 'addrFrom': tmp[1],'addrTo': tmp[2],'mask': tmp[3]})
		elif line[2:16] == "service-policy":
			pass
		else:
			log.write("\nObject type = Interface\nObject Name = %s\nIssue = Encountered an unhandeled command (%s).\nPlease address manually!\n" % (name, line) )
	text = re.sub(str_interface[:-1], '', text)
	# end of for loop
#end interface

for trap in re.findall('^snmp-server host.+\n', text, re.MULTILINE):
	snmp_trap_id+=1
	text=text.replace(trap,'')
	trap = trap.split()
	if snmp_trap_id<=2:
		dict_sys['ssnmp'].update({"trap"+str(snmp_trap_id): trap[2]})
	else:
		log.write("\nObject type = Interface\nObject Name = %s\nIssue = Only 2 SNMP trap hosts are supported.\nPlease address manually!\n" % (name, line) )
#end pmap

for line in text.splitlines():
	if line[0:13] == "login timeout":
		dict_sys.update({'idle': line[14:]})
		text=text.replace(line,'')

### OUTPUTS ###
for x in dict_interface:
	output.write("/c/l3/if "+str(x)+"\n")
	for y in dict_interface[x]:
		output.write("  %s %s\n" % (y, dict_interface[x][y]))

for x in dict_advhc:
	output.write("/c/slb/advhc/health "+x+"\n")
	for y in dict_advhc[x]:
		output.write("  %s %s\n" % (y, dict_advhc[x][y]))

for x in dict_reals:
	output.write("/c/slb/real "+x+"\n")
	for y in dict_reals[x]:
		output.write("  %s %s\n" % (y, dict_reals[x][y]))

for x in dict_group:
	output.write("/c/slb/group "+x+"\n")
	for y in dict_group[x]:
		output.write("  %s %s\n" % (y, dict_group[x][y]))

for x in dict_virt:
	output.write("/c/slb/virt "+x+"\n")
	for y in dict_virt[x]:
		output.write("  %s %s\n" % (y, dict_virt[x][y]))

if len(dict_route) > 0:
	output.write("/c/l3/route/ip4 \n")
	for x in dict_route:
		output.write("  add %s %s %s\n" % (dict_route[x]['dst'], dict_route[x]['mask'], dict_route[x]['gw']))
c=0
for x in list_gw:
	c+=1
	output.write("/c/l3/gw %d\n" % c)
	output.write("  ena\n  ipver v4\n  addr %s\n" % x)

for x in dict_sys:
	if type(dict_sys[x])==dict:
		output.write("/c/sys/%s\n" % x)
		for y in dict_sys[x]:
			output.write("  %s %s\n" % (y, dict_sys[x][y]))
	else:
		output.write("/c/sys\n  %s %s\n" % (x, dict_sys[x]))



while '\n\n' in text:
	text=text.replace('\n\n', '\n')
leftovers.write(text)