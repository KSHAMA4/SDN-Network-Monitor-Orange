from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.recoco import Timer
from pox.lib.util import dpid_to_str

log = core.getLogger()

class OrangeMonitor(object):
    def __init__(self):
        core.openflow.addListeners(self)
        self.stats = {} # Stores {port_no: last_byte_count}
        
        # Periodic Timer: Trigger _request_stats every 5 seconds
        Timer(5, self._request_stats, recurring=True)

    def _request_stats(self):
        for connection in core.openflow._connections.values():
            # Send an OpenFlow Stats Request to the switch
            connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
        log.debug("Stats request sent to switches")

    def _handle_PortStatsReceived(self, event):
        """
        This function handles the reply from the switch.
        It calculates bandwidth: (Current Bytes - Previous Bytes) / Time
        """
        print(f"\n--- Network Utilization (Switch {dpid_to_str(event.dpid)}) ---")
        
        for stat in event.stats:
            port = stat.port_no
            if port > 60000: continue # Ignore internal/local ports
            
            # Combine Rx (Received) and Tx (Transmitted) bytes
            total_bytes = stat.rx_bytes + stat.tx_bytes
            
            if port in self.stats:
                prev_bytes = self.stats[port]
                # Calculation: (Byte Difference * 8 bits) / 5 seconds
                bandwidth = (total_bytes - prev_bytes) * 8 / 5
                print(f" Port {port}: Utilization = {bandwidth:.2f} bits/sec")
            
            # Update the stored byte count for the next interval
            self.stats[port] = total_bytes

    def _handle_ConnectionUp(self, event):
        log.info("Switch %s connected. Monitoring started.", dpid_to_str(event.dpid))

def launch():
    # We load 'forwarding.l2_learning' so the switch knows how to forward packets
    # while our 'orange_monitor' handles the statistics.
    core.registerNew(OrangeMonitor)
    log.info("Orange Monitor Module Loaded.")
