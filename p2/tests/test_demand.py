import unittest
from types import SimpleNamespace as NS
from p2.prepare_demand import route_candidates, xml_route_candidates
import xml.etree.ElementTree as ET


class DemandTests(unittest.TestCase):
    def test_only_connected_passenger_paths_become_routes(self):
        edges={name:NS(getID=lambda name=name:name,allows=lambda mode:mode=='passenger') for name in ('a','b')}
        net=NS(getLane=lambda lane:NS(getEdge=lambda:edges[lane]),
               getShortestPath=lambda start,finish,**kwargs:([start,finish],10))
        mapping=[{'missing_signal_ids':[],'sumo_tls_ids':[tls]} for tls in ('1','2')]
        programs=[{'tls_id':tls,'controlled_links':[{'from_lane_id':lane}]} for tls,lane in (('1','a'),('2','b'))]
        routes,connections=route_candidates(net,mapping,programs)
        self.assertEqual(len(routes),2)
        self.assertTrue(all(row['path_found'] for row in connections))

    def test_missing_signal_mapping_fails_before_routing(self):
        with self.assertRaises(ValueError):
            route_candidates(None,[{'missing_signal_ids':['960'],'sumo_tls_ids':['1']}],[])

    def test_xml_routes_respect_lane_permissions_and_connections(self):
        root=ET.fromstring('''<net><edge id="a"><lane id="a_0" index="0"/></edge>
        <edge id="b"><lane id="b_0" index="0" allow="passenger"/></edge>
        <edge id="walk"><lane id="walk_0" index="0" allow="pedestrian"/></edge>
        <connection from="a" fromLane="0" to="b" toLane="0"/>
        <connection from="b" fromLane="0" to="a" toLane="0"/>
        <connection from="a" fromLane="0" to="walk" toLane="0"/></net>''')
        mapping=[{'missing_signal_ids':[],'sumo_tls_ids':[tls]} for tls in ('1','2')]
        programs=[{'tls_id':tls,'controlled_links':[{'from_lane_id':lane}]} for tls,lane in (('1','a_0'),('2','b_0'))]
        routes,links=xml_route_candidates(root,mapping,programs)
        self.assertEqual(len(routes),2)
        self.assertTrue(all(row['path_found'] for row in links))
        self.assertTrue(all('walk' not in row['edges'] for row in routes))


if __name__=='__main__':
    unittest.main()
