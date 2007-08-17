
import comar
import logging


import ajan.ldaputil



class ServicePolicy(ajan.ldaputil.LdapClass):
    entries = (
        ("service_to_start", "comarServiceStart", list, None),
        ("service_to_stop", "comarServiceStop", list, None),
    )								


class Policy:
	
    def __init__( self ):
        self.policy = ServicePolicy()
        self.log = logging.getLogger("Mod.Service")
	
    def override(self, attr, is_ou=False):
        temp = ServicePolicy(attr)
	self.policy.service_to_start = temp.service_to_start
	self.policy.service_to_stop = temp.service_to_stop 
    
    def update(self, computer, units ):
        self.log.debug("Updating Service Policy")             
        self.policy = ServicePolicy()
        for unit in units:
            self.override(unit, True)
        self.override(computer)                    
        self.log.debug("Service policy is now:\n%s" % str(self.policy))
    
    
    def start_service ( self ):
	link = comar.Link()
	for service in self.policy.service_to_start:
        	link.System.Service[ service ].start()
        
    def stop_service ( self ):
    	link = comar.Link()
        for service in self.policy.service_to_stop:
		link.System.Service[service].stop()
	
    def apply(self):
        self.log.debug("Applying Service Policy" )
        self.start_service()
        self.stop_service()
 
