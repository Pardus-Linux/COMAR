 #G.Selda Kuruoglu

import comar                        # for 'comar's connection functions 
import logging                      # for log messages
import ajan.ldaputil                


class ServicePolicy(ajan.ldaputil.LdapClass):
    """ Service policy class has 2 attributes : service names to start, service names to stop """    
    entries = (
        ("service_to_start", "comarServiceStart", set, set()),
        ("service_to_stop", "comarServiceStop", set, set()),
    )


class Policy:
    def __init__(self):
        self.policy = ServicePolicy()
        self.log = logging.getLogger("Mod.Service")
    def override(self, attr, is_ou = False):
        """ Overrides service policy"""
        temp = ServicePolicy(attr)
        
        # Retrieve current service policy
        start_set = temp.service_to_start
        stop_set = temp.service_to_stop

        if is_ou:
            start_set.union (self.policy.service_to_start)
            stop_set.union (self.policy.service_to_stop)
        
        else:
            start_set = start_set.union (self.policy.service_to_start)
            start_set = start_set.difference (stop_set)

            stop_set = stop_set.union (self.policy.service_to_stop)
            stop_set = stop_set.difference (start_set)

        self.policy.service_to_start = start_set
        self.policy.service_to_stop = stop_set

    def update(self, computer, units ):
        """ Updates service policy"""
        self.log.debug("Updating Service Policy")             
        self.policy = ServicePolicy()
        for unit in units:
            self.override(unit, True)
        self.override(computer)                    
        self.log.debug("Service policy is now:\n%s" % str(self.policy))
    
    
    def start_service (self):
        """ starts sevices in 'service_to_start' list by connecting comar """
        link = comar.Link()
        for service in self.policy.service_to_start:
            link.System.Service[service].start()

    def stop_service (self):
        """ stops sevices in 'service_to_start' list by connecting comar """
        link = comar.Link()
        for service in self.policy.service_to_stop:
            link.System.Service[service].stop()

    def apply(self):
        self.log.debug("Applying Service Policy" )
        self.start_service()
        self.stop_service()
